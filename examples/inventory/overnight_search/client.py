"""Strong-backbone client; framework allocation $35, Baek allocation $12, reserve $3."""
import json
import math
import time
import urllib.request
import uuid

from ..correlated_benchmark.api_client import BudgetedClient, ModelRequestError, atomic_json


class SearchClient(BudgetedClient):
    def __init__(self, run_dir):
        super().__init__(run_dir, limit_usd=35., model="openai/gpt-5.6-sol", request_timeout=600)
        self.input_price_ceiling = 4.
        self.output_price_ceiling = 15.

    def chat(self, messages, max_tokens=10000, metadata=None):
        if (self.run_dir / "PAUSE").exists():
            raise ModelRequestError("Paused")
        if not 1 <= max_tokens <= 32768:
            raise ValueError("Invalid token ceiling")
        request_id = uuid.uuid4().hex
        payload = dict(model=self.model, messages=messages, max_tokens=max_tokens,
                       reasoning={"effort": "high"}, stream=False,
                       provider={"max_price": {"prompt": 4., "completion": 15., "request": 0},
                                 "require_parameters": True, "allow_fallbacks": False})
        folder = self.run_dir / "api_requests" / request_id
        folder.mkdir(parents=True)
        atomic_json(folder / "request.json", {"payload": payload, "metadata": metadata or {}})
        upper = self._reserve(request_id, messages, max_tokens, metadata)
        key = json.loads(self.credentials_path.read_text())["api_key"]
        request = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                     data=json.dumps(payload).encode(), method="POST",
                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        start = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
                result = json.loads(response.read())
        except Exception as exc:
            self._finish(request_id, "unknown_charge", error_type=type(exc).__name__,
                         http_status=getattr(exc, "code", None))
            raise ModelRequestError(f"Request failed: {type(exc).__name__}; reservation retained") from None
        finally:
            del key
        atomic_json(folder / "response.json", result)
        usage = result.get("usage", {})
        cost = usage.get("cost")
        known = type(cost) in (float, int) and math.isfinite(cost) and cost >= 0
        self._finish(request_id, "complete" if known else "missing_cost",
                     actual_cost_usd=float(cost) if known else None,
                     usage=usage, generation_id=result.get("id"),
                     elapsed_seconds=time.monotonic()-start,
                     reservation_exceeded=bool(known and cost > upper + 1e-9))
        if known and cost > upper + 1e-9:
            (self.run_dir / "PAUSE").touch()
            raise ModelRequestError("Price reservation exceeded")
        if not known:
            raise ModelRequestError("Authoritative cost missing; reservation retained")
        if result.get("model") != self.model:
            raise ModelRequestError("Model identity mismatch")
        content = result.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise ModelRequestError("No final content")
        return content, {**usage, "request_id": request_id,
                         "finish_reason": result.get("choices",[{}])[0].get("finish_reason")}
