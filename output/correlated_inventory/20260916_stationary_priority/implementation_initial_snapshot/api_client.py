"""Audited OpenRouter client with a shared, persistent USD budget.

Credentials are read only in the parent process at request time. Unknown charges
retain the entire reservation; neither transport retries nor restarts erase them.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import uuid


MODEL = "deepseek/deepseek-chat-v3-0324"
DEFAULT_CREDENTIALS = Path.home() / ".config/ahd4inventory/openrouter_credentials.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("w") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


class BudgetExceeded(RuntimeError):
    pass


class ModelRequestError(RuntimeError):
    pass


class BudgetedClient:
    def __init__(self, run_dir, limit_usd=20.0, model=MODEL,
                 credentials_path=DEFAULT_CREDENTIALS, request_timeout=180):
        self.run_dir = Path(run_dir).resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.limit_usd = float(limit_usd)
        self.model = model
        self.credentials_path = Path(credentials_path)
        self.request_timeout = request_timeout
        # OpenRouter enforces these ceilings in USD per million tokens.
        self.input_price_ceiling = 0.50
        self.output_price_ceiling = 1.20
        with self._ledger() as ledger:
            if ledger and ledger["limit_usd"] != self.limit_usd:
                raise ValueError("Budget differs from frozen ledger")
            if not ledger:
                ledger.update(limit_usd=self.limit_usd, model=self.model,
                              created_utc=utc_now(), requests={})
            if ledger["model"] != model:
                raise ValueError("Model differs from frozen ledger")

    @contextmanager
    def _ledger(self):
        with (self.run_dir / "api_budget.lock").open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            target = self.run_dir / "api_budget.json"
            ledger = json.loads(target.read_text()) if target.exists() else {}
            try:
                yield ledger
                atomic_json(target, ledger)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def summary(self):
        with self._ledger() as ledger:
            records = list(ledger["requests"].values())
            known = sum(r.get("actual_cost_usd", 0) or 0 for r in records)
            held = sum(r["reserved_usd"] for r in records if r["state"] in
                       {"pending", "unknown_charge", "missing_cost"})
            return dict(limit_usd=self.limit_usd, known_cost_usd=known,
                        held_upper_usd=held, committed_upper_usd=known + held,
                        requests=len(records), completed=sum(r["state"] == "complete" for r in records),
                        uncertain=sum(r["state"] in {"unknown_charge", "missing_cost"} for r in records))

    def _reserve(self, request_id, messages, max_tokens, metadata):
        # Ordinary text tokens cannot outnumber UTF-8 input bytes, with generous
        # framing overhead. Cap provider prices and output tokens in the request.
        input_bound = len(json.dumps(messages, ensure_ascii=False).encode()) + 1024
        upper = (input_bound * self.input_price_ceiling +
                 max_tokens * self.output_price_ceiling) / 1_000_000
        with self._ledger() as ledger:
            committed = sum(r["reserved_usd"] if r["state"] in
                            {"pending", "unknown_charge", "missing_cost"}
                            else (r.get("actual_cost_usd", 0) or 0)
                            for r in ledger["requests"].values())
            if committed + upper > self.limit_usd:
                raise BudgetExceeded(f"USD budget exhausted: committed={committed:.6f}, next_bound={upper:.6f}")
            ledger["requests"][request_id] = dict(
                state="pending", created_utc=utc_now(), reserved_usd=upper,
                input_token_bound=input_bound, max_output_tokens=max_tokens,
                metadata=metadata or {})
        return upper

    def _finish(self, request_id, state, **details):
        with self._ledger() as ledger:
            ledger["requests"][request_id].update(state=state, finished_utc=utc_now(), **details)

    def chat(self, messages, max_tokens=4096, temperature=.7, metadata=None):
        if (self.run_dir / "PAUSE").exists():
            raise ModelRequestError("Experiment paused before request submission")
        if not 1 <= max_tokens <= 8192:
            raise ValueError("Output token cap must be between 1 and 8192")
        if any(not isinstance(m.get("content"), str) for m in messages):
            raise ValueError("Only text messages are permitted")
        request_id = uuid.uuid4().hex
        key = json.loads(self.credentials_path.read_text())["api_key"]
        payload = dict(model=self.model, messages=messages, max_tokens=max_tokens,
                       temperature=temperature, stream=False,
                       provider={"max_price": {"prompt": self.input_price_ceiling,
                                                "completion": self.output_price_ceiling,
                                                "request": 0}, "require_parameters": True})
        folder = self.run_dir / "api_requests" / request_id
        folder.mkdir(parents=True)
        atomic_json(folder / "request.json", dict(payload=payload, metadata=metadata or {}))
        upper = self._reserve(request_id, messages, max_tokens, metadata)
        request = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                    data=json.dumps(payload).encode(), method="POST",
                    headers={"Authorization": "Bearer " + key,
                             "Content-Type": "application/json",
                             "User-Agent": "AHD4Inventory-correlated-benchmark/1.0"})
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            # Authentication, routing and rate-limit rejections occur before
            # inference. A server failure may have incurred cost.
            rejected = exc.code in {400, 401, 402, 403, 404, 422, 429}
            self._finish(request_id, "rejected" if rejected else "unknown_charge",
                         http_status=exc.code, **({"actual_cost_usd": 0.0} if rejected else {}))
            raise ModelRequestError(f"OpenRouter HTTP {exc.code}; request={request_id}") from None
        except Exception as exc:
            self._finish(request_id, "unknown_charge", error_type=type(exc).__name__)
            raise ModelRequestError(f"OpenRouter transport failure ({type(exc).__name__}); request={request_id}; reservation retained") from None
        finally:
            del key
        usage = result.get("usage", {})
        cost = usage.get("cost")
        cost_valid = isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0
        safe_result = {k: result.get(k) for k in ("id", "model", "provider", "choices", "usage", "error")}
        atomic_json(folder / "response.json", safe_result)
        self._finish(request_id, "complete" if cost_valid else "missing_cost",
                     generation_id=result.get("id"), provider=result.get("provider"),
                     actual_cost_usd=float(cost) if cost_valid else None,
                     elapsed_seconds=time.monotonic() - started,
                     usage=usage, reservation_exceeded=bool(cost_valid and cost > upper + 1e-9))
        if cost_valid and cost > upper + 1e-9:
            raise ModelRequestError("Observed charge exceeded provider-bound reservation; stop for accounting review")
        choices = result.get("choices") or []
        content = choices[0].get("message", {}).get("content") if choices else None
        if not isinstance(content, str) or not content.strip():
            raise ModelRequestError(f"Empty model response; request={request_id}")
        return content, {**usage, "request_id": request_id, "model": result.get("model"),
                         "provider": result.get("provider"), "finish_reason": choices[0].get("finish_reason")}
