"""Auditable OpenRouter Responses sessions; no paid request runs on import.

The caller supplies the API key in memory and persists the shared RunBudget.
There are no automatic retries, provider fallbacks, or format-repair requests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import ast
import json
import math
from pathlib import Path
import re
import time
import threading
from typing import Any, Callable
import urllib.error
import urllib.request

try:
    from .sandbox import PythonSandbox
except ImportError:
    from sandbox import PythonSandbox


class BudgetExceeded(RuntimeError):
    pass


class UnresolvedRequestError(RuntimeError):
    """A POST has no durable response; resuming must never silently repeat it."""
    pass


_BUDGET_LOCK = threading.RLock()


@dataclass
class RunBudget:
    limit_usd: float
    spent_usd: float = 0.0
    reserved_usd: float = 0.0

    def require_available(self, upper_cost: float) -> None:
        with _BUDGET_LOCK:
            if upper_cost < 0 or self.spent_usd + self.reserved_usd + upper_cost > self.limit_usd + 1e-12:
                raise BudgetExceeded("Request upper cost exceeds remaining shared run budget")

    def reserve(self, upper_cost: float) -> None:
        with _BUDGET_LOCK:
            self.require_available(upper_cost)
            self.reserved_usd += upper_cost

    def settle(self, upper_cost: float, actual_cost: float | None) -> None:
        with _BUDGET_LOCK:
            self.reserved_usd = max(0.0, self.reserved_usd - upper_cost)
            # Unknown outcomes retain the entire reservation as conservatively spent.
            self.spent_usd += upper_cost if actual_cost is None else actual_cost

    def charge(self, actual_cost: float) -> None:
        with _BUDGET_LOCK:
            self.spent_usd += actual_cost


@dataclass
class SessionConfig:
    level: str = "L1"
    model: str = "openai/gpt-5.6-sol"
    max_tool_calls: int = 50
    python_budget_seconds: float = 3600.0
    request_timeout_seconds: float = 3600.0

    def __post_init__(self):
        if self.level not in {"L1", "L2"}:
            raise ValueError("level must be L1 or L2")
        if not 1 <= self.max_tool_calls <= 50 or not 0 < self.python_budget_seconds <= 3600:
            raise ValueError("Configuration exceeds the approved tool protocol")

    @property
    def max_output_tokens(self) -> int:
        return 16384 if self.level == "L1" else 32768


@dataclass
class SessionResult:
    status: str
    final_text: str = ""
    final_code: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    tool_calls: int = 0
    python_seconds: float = 0.0
    requests: int = 0
    actual_models: list[str] = field(default_factory=list)
    error: str | None = None
    http_status: int | None = None
    uncertain_cost_usd: float = 0.0
    interruption_waste_seconds: float = 0.0


PYTHON_TOOL = {
    "type": "function", "name": "run_python",
    "description": "Run Python in a fresh isolated process with standard library, NumPy and SciPy. No network or external files. State and files do not persist between calls. Output and remaining cumulative execution budget are returned.",
    "parameters": {"type": "object", "properties": {"code": {"type": "string"}},
                   "required": ["code"], "additionalProperties": False},
    "strict": True,
}


def extract_final_code(text: str) -> str | None:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.DOTALL)
    candidates = list(reversed(blocks)) if blocks else [text]
    for code in candidates:
        try:
            tree = ast.parse(code.strip())
        except SyntaxError:
            continue
        if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and
               node.name in {"compute_order_amount", "design"} for node in tree.body):
            return code.strip() + "\n"
    return None


class OpenRouterHarness:
    def __init__(self, *, api_key: str, sandbox: PythonSandbox, budget: RunBudget,
                 log_path: Path | str, config: SessionConfig | None = None,
                 transport: Callable[[dict[str, Any], str], dict[str, Any]] | None = None):
        if not api_key:
            raise ValueError("An in-memory API key is required")
        self._api_key = api_key
        self.sandbox, self.budget = sandbox, budget
        self.log_path = Path(log_path)
        self.config = config or SessionConfig()
        self.transport = transport or self._http_response

    def _redact(self, value):
        if isinstance(value, str):
            return value.replace(self._api_key, "[REDACTED]")
        if isinstance(value, dict):
            return {str(k): self._redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact(v) for v in value]
        return value

    def _log(self, event: str, **fields):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(self._redact({"event": event, "timestamp": time.time(), **fields}),
                                    ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()

    def _http_response(self, payload, api_key):
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/responses",
            data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json",
                     "X-OpenRouter-Metadata": "enabled"},
        )
        # urllib does not retry POST on transient HTTP/provider errors.
        with urllib.request.urlopen(request, timeout=self.config.request_timeout_seconds) as response:
            return json.load(response)

    def _payload(self, history, tools_enabled=True):
        payload = {
            "model": self.config.model, "input": history, "tools": [PYTHON_TOOL],
            "reasoning": {"effort": "high", "summary": "auto"}, "max_output_tokens": self.config.max_output_tokens,
            "include": ["reasoning.encrypted_content"], "store": False,
            "provider": {"order": ["OpenAI"], "allow_fallbacks": False,
                         "require_parameters": True, "sort": "price",
                         "max_price": {"prompt": 4, "completion": 15}},
        }
        if not tools_enabled:
            payload.pop("tools")
        return payload

    @staticmethod
    def cost_upper_bound(payload):
        # UTF-8 byte count + framing reserve deliberately overestimates input
        # tokens. Encrypted reasoning is included in the serialized history.
        input_upper = len(json.dumps(payload, ensure_ascii=False).encode()) + 4096
        output_upper = payload["max_output_tokens"]
        # Provider price ceilings, conservative even below the 272k threshold.
        upper = (input_upper * 4 + output_upper * 15) / 1_000_000
        normal_estimate = (input_upper * (4 if input_upper > 272000 else 2) +
                           output_upper * (15 if input_upper > 272000 else 10)) / 1_000_000
        return input_upper, upper, normal_estimate

    def _execute_calls(self, calls, history, result):
        for call in calls:
            remaining = self.config.python_budget_seconds - result.python_seconds
            if result.tool_calls >= self.config.max_tool_calls or remaining <= 0:
                tool_result = {"error": "Python tool budget exhausted; submit final source now",
                               "remaining_calls": 0, "remaining_seconds": max(0, remaining)}
            else:
                result.tool_calls += 1
                try:
                    if call.get("name") != "run_python":
                        raise ValueError("Unknown tool")
                    args = json.loads(call.get("arguments", "{}"))
                    execution = self.sandbox.run(args["code"], remaining)
                    result.python_seconds += execution.elapsed_seconds
                    tool_result = execution.to_dict()
                except Exception as exc:
                    tool_result = {"error": f"{type(exc).__name__}: {exc}"}
                tool_result.update(remaining_calls=self.config.max_tool_calls - result.tool_calls,
                                   remaining_seconds=max(0, self.config.python_budget_seconds-result.python_seconds))
            self._log("tool_result", call=call, result=tool_result)
            history.append({"type": "function_call_output", "call_id": call["call_id"],
                            "output": json.dumps(tool_result)})

    def _read_checkpoint(self, prompt):
        events = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise UnresolvedRequestError("Partial event log must be repaired before resuming") from exc
        starts = [e for e in events if e.get("event") == "session_start"]
        if len(starts) != 1 or starts[0].get("prompt") != prompt:
            raise ValueError("Checkpoint prompt differs from the original session")
        saved_config = starts[0].get("config", {})
        for key in ("level", "model", "max_tool_calls", "python_budget_seconds"):
            if saved_config.get(key) != getattr(self.config, key):
                raise ValueError("Checkpoint configuration differs: " + key)
        result = SessionResult(status="running")
        history = [{"role": "user", "content": prompt}]
        pending_request = None
        last_response = None
        terminal = None
        counted_tools = set()
        for event in events:
            kind = event.get("event")
            if kind == "request":
                if pending_request is not None:
                    raise UnresolvedRequestError("Multiple unresolved POSTs in checkpoint")
                pending_request = event
                result.requests += 1
                history = event["payload"]["input"].copy()
            elif kind == "response":
                if pending_request is None:
                    raise ValueError("Response has no preceding request")
                response = event["response"]
                usage = response.get("usage") or {}
                cost = usage.get("cost")
                if not isinstance(cost, (int, float)) or cost < 0:
                    raise UnresolvedRequestError("Logged response has no authoritative cost")
                result.cost_usd += float(cost)
                for name in ("input_tokens", "output_tokens", "total_tokens"):
                    result.usage[name] = result.usage.get(name, 0) + int(usage.get(name, 0))
                result.usage["last_response_usage"] = usage
                model = response.get("model")
                if not isinstance(model, str) or not (model in {"openai/gpt-5.6-sol", "gpt-5.6-sol"} or
                        model.startswith("openai/gpt-5.6-sol-") or model.startswith("gpt-5.6-sol-")):
                    raise ValueError("Checkpoint response has an unexpected model")
                if model and model not in result.actual_models:
                    result.actual_models.append(model)
                output = response.get("output") or []
                if not isinstance(output, list):
                    raise ValueError("Invalid checkpoint response output")
                history.extend(output)
                last_response = response
                pending_request = None
            elif kind == "tool_result":
                call, tool_result = event["call"], event["result"]
                call_id = call["call_id"]
                if call_id in counted_tools:
                    raise ValueError("Duplicate completed tool call in checkpoint: " + call_id)
                counted_tools.add(call_id)
                if not str(tool_result.get("error", "")).startswith("Python tool budget exhausted"):
                    result.tool_calls += 1
                result.python_seconds += float(tool_result.get("elapsed_seconds", 0.0))
                history.append({"type": "function_call_output", "call_id": call_id,
                                "output": json.dumps(tool_result)})
            elif kind == "tool_interrupted":
                result.interruption_waste_seconds += float(event.get("wasted_active_seconds", 0.0))
            elif kind == "request_interrupted":
                if pending_request is None:
                    raise ValueError("Interrupted request has no outstanding POST")
                result.uncertain_cost_usd += float(event["reserved_cost_retained_usd"])
                pending_request = None
            elif kind == "uncertain_paid_failure":
                result.uncertain_cost_usd += float(event.get("reserved_cost_retained_usd", 0.0))
                pending_request = None
            elif kind == "request_rejected" and event.get("known_pre_inference"):
                pending_request = None
            elif kind == "session_end":
                terminal = event["result"]
        return result, history, pending_request, last_response, terminal

    def record_request_interruption(self, prompt: str, *, interruption_id: str, reason: str):
        """Explicit accounting only; never sends a replacement POST.

        The external run budget must already retain this outstanding request's
        reservation via recover_spend. Recovery clears the pending marker and
        charges the upper amount exactly once after this event is appended.
        """
        if not interruption_id or not reason:
            raise ValueError("An explicit interruption ID and reason are required")
        _, _, pending, _, _ = self._read_checkpoint(prompt)
        if pending is None:
            raise ValueError("No outstanding request to mark interrupted")
        self._log("request_interrupted", interruption_id=interruption_id, reason=reason,
                  request_index=pending.get("request_index"), response_unavailable=True,
                  reserved_cost_retained_usd=pending["max_request_cost_usd"])

    def resume_from_log(self, prompt: str) -> SessionResult:
        """Resume a durable checkpoint, without repeating completed calls.

        An externally continued sandbox process must have its real tool_result
        appended before invoking this method. Pending function calls with no
        tool_result are executed once before the next API request. Paused wall
        time is excluded by the external monitor's elapsed_seconds value.
        """
        result, history, pending, last_response, terminal = self._read_checkpoint(prompt)
        if pending is not None:
            raise UnresolvedRequestError("An outstanding API request has no response; capture or explicitly reconcile it before resuming")
        if terminal is not None:
            fields = SessionResult.__dataclass_fields__
            return SessionResult(**{key: value for key, value in terminal.items() if key in fields})
        completed_ids = {item["call_id"] for item in history if item.get("type") == "function_call_output"}
        pending_calls = [item for item in history if item.get("type") == "function_call" and item["call_id"] not in completed_ids]
        if not math.isfinite(result.python_seconds) or result.python_seconds < 0 or result.tool_calls > self.config.max_tool_calls:
            raise ValueError("Checkpoint contains invalid tool accounting")
        self._log("session_resumed", completed_requests=result.requests, completed_tool_calls=result.tool_calls,
                  productive_python_seconds=result.python_seconds, interruption_waste_seconds=result.interruption_waste_seconds,
                  pending_tool_call_ids=[call["call_id"] for call in pending_calls], budget=asdict(self.budget))
        if last_response is not None and not any(item.get("type") == "function_call" for item in last_response.get("output", [])):
            result.final_text = "\n".join(part.get("text", "") for item in last_response.get("output", [])
                                             if item.get("type") == "message" for part in item.get("content", [])
                                             if part.get("type") == "output_text")
            result.final_code = extract_final_code(result.final_text)
            result.status = "completed" if result.final_code and last_response.get("status", "completed") == "completed" else "invalid_final_output"
            self._log("session_end", result=asdict(result), budget=asdict(self.budget))
            return result
        return self.run(prompt, _checkpoint=(result, history, pending_calls))

    def run(self, prompt: str, *, _checkpoint=None) -> SessionResult:
        self.sandbox.probe()
        if _checkpoint is None:
            result = SessionResult(status="running")
            history: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
            self._log("session_start", config=asdict(self.config), prompt=prompt,
                      budget=asdict(self.budget), protocol="openrouter-responses-stateless")
        else:
            result, history, pending_calls = _checkpoint
            self._execute_calls(pending_calls, history, result)
        while True:
            tools_enabled = (result.tool_calls < self.config.max_tool_calls and
                             result.python_seconds < self.config.python_budget_seconds)
            payload = self._payload(history, tools_enabled=tools_enabled)
            input_upper, upper, estimated = self.cost_upper_bound(payload)
            try:
                self.budget.reserve(upper)
            except BudgetExceeded as exc:
                result.status, result.error = "budget_exhausted", str(exc)
                break
            self._log("request", request_index=result.requests, payload=payload,
                      input_tokens_upper=input_upper, max_request_cost_usd=upper,
                      normal_price_estimate_usd=estimated, budget=asdict(self.budget))
            started = time.monotonic()
            result.requests += 1
            try:
                response = self.transport(payload, self._api_key)
            except urllib.error.HTTPError as exc:
                result.http_status = int(exc.code)
                try:
                    raw_body = exc.read(1_048_577)
                    body_text = raw_body[:1_048_576].decode("utf-8", errors="replace")
                    if len(raw_body) > 1_048_576:
                        body_text += "\n[HTTP error body truncated]"
                except Exception as read_error:
                    body_text = f"[error body unavailable: {type(read_error).__name__}]"
                finally:
                    exc.close()
                try:
                    error_body = json.loads(body_text)
                except json.JSONDecodeError:
                    error_body = body_text
                result.error = self._redact(f"HTTP {exc.code}: {body_text}")
                metadata = error_body.get("openrouter_metadata", {}) if isinstance(error_body, dict) else {}
                error_info = error_body.get("error", {}) if isinstance(error_body, dict) else {}
                endpoints = metadata.get("endpoints", {}).get("available", [])
                known_routing_rejection = (
                    exc.code == 404 and isinstance(error_info, dict)
                    and str(error_info.get("message", "")).startswith("No endpoints found")
                    and bool(error_info.get("metadata", {}).get("failed_routing_step"))
                    and metadata.get("attempt") == 0 and bool(endpoints)
                    and all(endpoint.get("selected") is False for endpoint in endpoints)
                )
                if known_routing_rejection:
                    # Explicit routing metadata proves no provider was selected.
                    # Other HTTP failures retain their reservation until reconciled.
                    self.budget.settle(upper, 0.0)
                    result.status = "transport_rejected"
                    self._log("request_rejected", http_status=exc.code, error_body=error_body,
                              elapsed_seconds=time.monotonic()-started, known_pre_inference=True,
                              charge_usd=0.0, released_reservation_usd=upper, budget=asdict(self.budget))
                else:
                    self.budget.settle(upper, None)
                    result.status = "uncertain_paid_failure"
                    self._log("uncertain_paid_failure", http_status=exc.code, error_body=error_body,
                              error=result.error, elapsed_seconds=time.monotonic()-started,
                              reserved_cost_retained_usd=upper, budget=asdict(self.budget))
                break
            except Exception as exc:
                self.budget.settle(upper, None)
                result.status = "uncertain_paid_failure"
                result.error = f"{type(exc).__name__}: {exc}"
                self._log("uncertain_paid_failure", error=result.error, elapsed_seconds=time.monotonic()-started,
                          reserved_cost_retained_usd=upper, budget=asdict(self.budget))
                break
            self._log("response", response=response, elapsed_seconds=time.monotonic()-started)
            usage = response.get("usage") or {}
            actual_cost = usage.get("cost")
            if not isinstance(actual_cost, (float, int)) or actual_cost < 0:
                self.budget.settle(upper, None)
                result.status, result.error = "missing_authoritative_cost", "usage.cost missing; stopped with reservation retained"
                break
            self.budget.settle(upper, float(actual_cost))
            result.cost_usd += float(actual_cost)
            for name in ("input_tokens", "output_tokens", "total_tokens"):
                result.usage[name] = result.usage.get(name, 0) + int(usage.get(name, 0))
            result.usage["last_response_usage"] = usage
            model = response.get("model")
            if model and model not in result.actual_models:
                result.actual_models.append(model)
            if not isinstance(model, str) or not (model == "openai/gpt-5.6-sol" or model == "gpt-5.6-sol" or
                                                  model.startswith("openai/gpt-5.6-sol-") or model.startswith("gpt-5.6-sol-")):
                result.status, result.error = "unexpected_model", "Provider returned a different or missing model identifier"
                break
            if actual_cost > upper + 1e-9 or self.budget.spent_usd > self.budget.limit_usd + 1e-9:
                result.status, result.error = "cost_bound_exceeded", "Authoritative cost exceeded conservative request reservation"
                break
            output = response.get("output") or []
            if not isinstance(output, list):
                result.status, result.error = "invalid_response", "Response output is not a list"
                break
            # Preserve full reasoning/encrypted content and call IDs verbatim.
            history.extend(output)
            calls = [item for item in output if item.get("type") == "function_call"]
            if calls and not tools_enabled:
                result.status, result.error = "tool_limit_repeated", "Model requested tools after final submission request"
                break
            result.final_text = "\n".join(part.get("text", "") for item in output
                                             if item.get("type") == "message"
                                             for part in item.get("content", [])
                                             if part.get("type") == "output_text")
            if not calls:
                result.final_code = extract_final_code(result.final_text)
                result.status = "completed" if result.final_code and response.get("status", "completed") == "completed" else "invalid_final_output"
                break
            self._execute_calls(calls, history, result)
            # Only one final submission request once tools are exhausted.
            if result.requests > self.config.max_tool_calls + 1:
                result.status, result.error = "tool_limit_repeated", "Model continued tool requests after budget exhaustion"
                break
        self._log("session_end", result=asdict(result), budget=asdict(self.budget))
        return result
