"""Opt-in Chat Completions client with one shared, durable dollar ledger.

Importing or constructing this module never sends a request. Live calls require
both endpoint_confirmed=True and allow_network=True. No model ID, endpoint or
price is guessed. Peak prices may be frozen as conservative upper estimates;
estimated charges are always distinguished from provider-reported charges.

Credentials must be an external, owner-only 0600 JSON file:
    {"credentials": [{"api_key": "...", "allowed_origin": "https://api.example.com"}]}
Only the explicitly selected index is used. There is no key rotation, automatic
POST retry, redirect following, policy execution or hidden-reasoning persistence.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading
import time
from typing import Callable
import urllib.error
import urllib.parse
import urllib.request
import uuid


REPO = Path(__file__).resolve().parents[3]
_LOCKS_GUARD = threading.Lock()
_LOCKS: dict[str, threading.RLock] = {}
_UNIT = Decimal(1_000_000)
_SYSTEM = ("Return only the requested Python source code, optionally in separate python code fences. "
           "Do not include explanations, analysis, hidden reasoning, or tool calls.")


class ClientError(RuntimeError):
    """A sanitized error; response bodies and credentials are never included."""


class BudgetExceeded(ClientError):
    pass


class ConfigurationError(ClientError):
    pass


class CredentialError(ClientError):
    pass


class ResponseError(ClientError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def amount(value):
    try:
        if isinstance(value, bool):
            raise ValueError
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise ValueError
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ConfigurationError("Dollar amounts must be finite and nonnegative") from None


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class FrozenPricing:
    input_uncached_usd_per_million: str | float
    input_cached_usd_per_million: str | float
    output_usd_per_million: str | float
    request_fee_usd: str | float = "0"
    estimate_is_upper_bound: bool = True

    def identity(self):
        if self.estimate_is_upper_bound is not True:
            raise ConfigurationError("Budget settlement requires frozen upper-bound prices")
        return {key: str(amount(getattr(self, key))) for key in (
            "input_uncached_usd_per_million", "input_cached_usd_per_million", "output_usd_per_million",
            "request_fee_usd")} | {"estimate_is_upper_bound": True, "currency": "USD"}

    def reserve(self, input_tokens, output_tokens):
        values = self.identity()
        price = max(amount(values["input_uncached_usd_per_million"]), amount(values["input_cached_usd_per_million"]))
        total = (Decimal(input_tokens) * price + Decimal(output_tokens) * amount(values["output_usd_per_million"])) / _UNIT
        return (total + amount(values["request_fee_usd"])).quantize(Decimal("0.000000000001"), rounding=ROUND_CEILING)


@dataclass(frozen=True)
class ClientConfig:
    client_id: str
    endpoint: str
    model: str
    pricing: FrozenPricing
    endpoint_confirmed: bool = False
    allowed_returned_models: tuple[str, ...] = ()
    thinking_enabled: bool | None = None
    reasoning_effort: str | None = None
    reasoning_parameter: str = "reasoning_effort"
    max_tokens_parameter: str = "max_tokens"
    completion_tokens_include_reasoning: bool = True
    output_limit_includes_reasoning: bool = True
    request_timeout_seconds: float = 600.
    max_output_tokens_limit: int = 65536
    extra_body: dict | None = None

    def identity(self):
        endpoint_origin(self.endpoint)
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", self.client_id):
            raise ConfigurationError("client_id must be a short stable identifier")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ConfigurationError("An explicit model ID is required")
        if self.reasoning_parameter not in ("reasoning_effort", "reasoning"):
            raise ConfigurationError("Unsupported reasoning parameter style")
        if self.max_tokens_parameter not in ("max_tokens", "max_completion_tokens"):
            raise ConfigurationError("Unsupported output token parameter")
        if self.thinking_enabled is not None and type(self.thinking_enabled) is not bool:
            raise ConfigurationError("thinking_enabled must be a boolean or None")
        if self.reasoning_effort is not None and self.reasoning_effort not in ("none", "minimal", "low", "medium", "high", "xhigh", "max"):
            raise ConfigurationError("Unsupported configured reasoning effort")
        if self.output_limit_includes_reasoning is not True:
            raise ConfigurationError("The output-token ceiling must also cover billed reasoning tokens")
        if not isinstance(self.completion_tokens_include_reasoning, bool):
            raise ConfigurationError("Completion-token accounting semantics must be explicit")
        if amount(self.request_timeout_seconds) == 0:
            raise ConfigurationError("Request timeout must be positive")
        if type(self.max_output_tokens_limit) is not int or not 1 <= self.max_output_tokens_limit <= 1_000_000:
            raise ConfigurationError("Invalid maximum output-token limit")
        accepted = self.allowed_returned_models or (self.model,)
        if not all(isinstance(value, str) and value for value in accepted):
            raise ConfigurationError("Returned-model aliases must be explicit strings")
        extra = {} if self.extra_body is None else self.extra_body
        protected = {"model", "messages", "max_tokens", "max_completion_tokens", "stream", "n",
                     "reasoning", "reasoning_effort", "thinking", "tools", "tool_choice", "functions",
                     "function_call", "api_key", "authorization", "headers"}
        if not isinstance(extra, dict) or any(not isinstance(key, str) or key.lower() in protected for key in extra):
            raise ConfigurationError("extra_body cannot replace identity, messages, token/thinking controls or enable tools")
        try:
            extra = json.loads(canonical(extra))
        except (ValueError, TypeError):
            raise ConfigurationError("extra_body must be finite JSON") from None
        return dict(client_id=self.client_id, endpoint=self.endpoint, requested_model=self.model,
                    allowed_returned_models=list(accepted), pricing=self.pricing.identity(),
                    thinking_enabled=self.thinking_enabled, reasoning_effort=self.reasoning_effort,
                    reasoning_parameter=self.reasoning_parameter, max_tokens_parameter=self.max_tokens_parameter,
                    completion_tokens_include_reasoning=self.completion_tokens_include_reasoning,
                    output_limit_includes_reasoning=True, max_output_tokens_limit=self.max_output_tokens_limit,
                    request_timeout_seconds=float(self.request_timeout_seconds), extra_body=extra)


def endpoint_origin(endpoint):
    parsed = urllib.parse.urlsplit(endpoint)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not parsed.path.endswith("/chat/completions")):
        raise ConfigurationError("Provide an explicit HTTPS Chat Completions endpoint without credentials or query parameters")
    return f"{parsed.scheme}://{parsed.netloc}"


def read_credential(path, index, origin):
    path = Path(path).absolute()
    if type(index) is not int or index < 0:
        raise CredentialError("Choose one nonnegative credential index")
    if path.resolve().is_relative_to(REPO):
        raise CredentialError("Credentials must be stored outside the repository")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "r") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid():
                raise CredentialError("Credential file must be a regular, current-user-owned 0600 file")
            data = json.load(handle)
        selected = data["credentials"][index]
        if selected.get("allowed_origin") != origin:
            raise CredentialError("Selected credential is not bound to the configured endpoint origin")
        key = selected["api_key"]
        if not isinstance(key, str) or not key.strip() or "\r" in key or "\n" in key:
            raise CredentialError("Selected credential is invalid")
        return key
    except CredentialError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        raise CredentialError("Could not read the explicitly selected external credential") from None


class DurableDollarLedger:
    """Multiple models, threads and processes share one immutable USD limit."""
    def __init__(self, directory, limit_usd):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory / "budget.json"
        self.limit = amount(limit_usd)
        if self.limit <= 0:
            raise ConfigurationError("Shared budget must be positive")
        with _LOCKS_GUARD:
            self.thread_lock = _LOCKS.setdefault(str(self.path), threading.RLock())
        with self.locked() as ledger:
            if not ledger:
                ledger.update(version=1, currency="USD", limit_usd=str(self.limit), created_utc=utc_now(),
                              clients={}, requests={}, paused_reason=None)
            elif amount(ledger.get("limit_usd")) != self.limit or ledger.get("currency") != "USD":
                raise ConfigurationError("Shared budget allocation is immutable")

    @contextmanager
    def locked(self):
        with self.thread_lock:
            fd = os.open(self.directory / "budget.lock", os.O_RDWR | os.O_CREAT, 0o600)
            with os.fdopen(fd, "a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    try:
                        ledger = json.loads(self.path.read_text()) if self.path.exists() else {}
                    except (ValueError, OSError):
                        raise ConfigurationError("Shared budget ledger is unreadable; refusing to reset it") from None
                    yield ledger
                    atomic_json(self.path, ledger)
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def totals(ledger):
        actual = estimated = held = Decimal(0)
        for row in ledger["requests"].values():
            if row["state"] == "actual":
                actual += amount(row["actual_cost_usd"])
            elif row["state"] == "pricing_upper_estimate":
                estimated += amount(row["estimated_upper_usd"])
            else:
                held += amount(row["reserved_usd"])
        return actual, estimated, held

    def register(self, client_id, identity):
        with self.locked() as ledger:
            previous = ledger["clients"].get(client_id)
            if previous is not None and previous != identity:
                raise ConfigurationError("Client endpoint, model, pricing or credential selection differs from frozen configuration")
            ledger["clients"][client_id] = identity

    def reserve(self, client_id, upper, *, request_metadata):
        upper = amount(upper)
        request_id = uuid.uuid4().hex
        with self.locked() as ledger:
            if ledger.get("paused_reason"):
                raise BudgetExceeded("Shared model-comparison ledger is paused for accounting review")
            if client_id not in ledger["clients"]:
                raise ConfigurationError("Client is not registered in shared budget")
            if sum(self.totals(ledger)) + upper > self.limit:
                raise BudgetExceeded("Shared dollar budget cannot cover this request reservation")
            ledger["requests"][request_id] = dict(client_id=client_id, state="pending", reserved_usd=str(upper),
                                                reserved_utc=utc_now(), **request_metadata)
        return request_id

    def finish(self, request_id, *, state, pause_reason=None, **fields):
        if state not in ("actual", "pricing_upper_estimate", "unknown_charge"):
            raise ConfigurationError("Invalid settlement state")
        with self.locked() as ledger:
            row = ledger["requests"][request_id]
            if row["state"] != "pending":
                raise ConfigurationError("Request was already settled; refusing duplicate mutation")
            row.update(state=state, finished_utc=utc_now(), **fields)
            if pause_reason:
                ledger["paused_reason"] = pause_reason
            if sum(self.totals(ledger)) > self.limit:
                ledger["paused_reason"] = "Recorded fees exceed the shared allocation"

    def summary(self):
        with self.locked() as ledger:
            actual, estimated, held = self.totals(ledger)
            committed = actual + estimated + held
            return dict(limit_usd=float(self.limit), actual_cost_usd=float(actual),
                        estimated_upper_usd=float(estimated), held_upper_usd=float(held),
                        committed_upper_usd=float(committed), remaining_usd=float(max(Decimal(0), self.limit - committed)),
                        requests=len(ledger["requests"]), paused_reason=ledger.get("paused_reason"))


def _count(value):
    if type(value) is not int or value < 0:
        raise ResponseError("Token usage is missing or invalid")
    return value


def token_usage(usage, *, completion_includes_reasoning=True):
    """Normalize only numeric billing metadata, never reasoning text."""
    if not isinstance(usage, dict):
        raise ResponseError("Token usage is missing or invalid")
    prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion = usage.get("completion_tokens", usage.get("output_tokens"))
    details = usage.get("completion_tokens_details") or usage.get("output_tokens_details") or {}
    reasoning = details.get("reasoning_tokens", usage.get("reasoning_tokens")) if isinstance(details, dict) else None
    if reasoning is not None:
        reasoning = _count(reasoning)
    completion = _count(completion)
    if completion_includes_reasoning:
        if reasoning is not None and reasoning > completion:
            raise ResponseError("Reasoning tokens exceed the inclusive completion count")
        billed_output = completion
    else:
        # Never silently treat missing separate reasoning counts as zero.
        billed_output = completion + _count(reasoning)
    input_details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    hit = usage.get("prompt_cache_hit_tokens")
    if hit is None and isinstance(input_details, dict):
        hit = input_details.get("cached_tokens")
    miss = usage.get("prompt_cache_miss_tokens")
    cache_reported = hit is not None or miss is not None
    if prompt is None and hit is not None and miss is not None:
        prompt = _count(hit) + _count(miss)
    prompt = _count(prompt)
    if hit is None and miss is None:
        hit, miss = 0, prompt
    elif hit is None:
        miss = _count(miss)
        hit = prompt - miss
    elif miss is None:
        hit = _count(hit)
        miss = prompt - hit
    hit, miss = _count(hit), _count(miss)
    if hit + miss != prompt:
        raise ResponseError("Cached and uncached input counts do not sum to total input")
    return dict(prompt_tokens=prompt, completion_tokens=completion, reasoning_tokens=reasoning,
                billed_output_tokens=billed_output, prompt_cache_hit_tokens=hit, prompt_cache_miss_tokens=miss,
                cache_counts_reported=cache_reported, completion_tokens_include_reasoning=completion_includes_reasoning)


def estimate_charge(usage, pricing, *, completion_includes_reasoning=True):
    counts = token_usage(usage, completion_includes_reasoning=completion_includes_reasoning)
    rates = pricing.identity()
    hit_price = amount(rates["input_cached_usd_per_million"])
    miss_price = amount(rates["input_uncached_usd_per_million"])
    input_cost = (Decimal(counts["prompt_cache_hit_tokens"]) * hit_price
                  + Decimal(counts["prompt_cache_miss_tokens"]) * miss_price)
    if not counts["cache_counts_reported"]:
        input_cost = Decimal(counts["prompt_tokens"]) * max(hit_price, miss_price)
    total = (input_cost + Decimal(counts["billed_output_tokens"]) * amount(rates["output_usd_per_million"])) / _UNIT
    return total + amount(rates["request_fee_usd"]), counts


def extract_code_only(content):
    if not isinstance(content, str):
        raise ResponseError("The provider did not return text code content")
    # Some compatible providers put thinking in content instead of a separate
    # field. Strip known containers; an unclosed container is never persisted.
    for tag in ("think", "thinking", "analysis", "reasoning"):
        content = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}\s*>", "", content, flags=re.I | re.S)
        content = re.sub(rf"<{tag}\b[^>]*>.*$", "", content, flags=re.I | re.S)
        closing = list(re.finditer(rf"</{tag}\s*>", content, flags=re.I))
        if closing:
            content = content[closing[-1].end():]
    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", content, flags=re.S | re.I)
    candidates = blocks or [content.strip()]
    sources = []
    for code in candidates:
        code = code.strip() + "\n"
        try:
            tree = ast.parse(code)
        except (SyntaxError, ValueError, TypeError):
            raise ResponseError("Response does not contain complete Python code") from None
        if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for node in tree.body):
            raise ResponseError("Response lacks a Python function or class definition")
        sources.append(code)
    return "\n\n".join("```python\n" + code + "```" for code in sources), sources


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Redirects are disabled", headers, fp)


def _post_once(*, endpoint, payload, api_key, timeout):
    request = urllib.request.Request(endpoint, data=canonical(payload).encode(), method="POST", headers={
        "Authorization": "Bearer " + api_key, "Content-Type": "application/json",
        "User-Agent": "AHD4Inventory-model-comparison/1"})
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        # Failed decoding is an uncertain billed request, never a POST retry.
        return json.loads(response.read(16_000_001))


class ModelComparisonClient:
    def __init__(self, config: ClientConfig, budget_directory, limit_usd, credentials_path,
                 credential_index=0, *, allow_network=False, transport: Callable | None = None):
        self.config = config
        self.identity = config.identity()
        self.credentials_path = Path(credentials_path).absolute()
        if type(credential_index) is not int or credential_index < 0:
            raise ConfigurationError("Select a single nonnegative credential index")
        self.credential_index = credential_index
        self.allow_network = allow_network
        self.transport = transport
        self.ledger = DurableDollarLedger(budget_directory, limit_usd)
        self.ledger.register(config.client_id, dict(self.identity, credential_index=credential_index,
                                                 credentials_path=str(self.credentials_path)))

    def summary(self):
        return self.ledger.summary()

    def preview(self, messages, max_tokens=32768):
        if type(max_tokens) is not int or not 1 <= max_tokens <= self.config.max_output_tokens_limit:
            raise ConfigurationError("Output token ceiling is outside the frozen configuration")
        if not isinstance(messages, list) or not messages:
            raise ConfigurationError("Provide nonempty text messages")
        clean = [dict(role="system", content=_SYSTEM)]
        for row in messages:
            if (not isinstance(row, dict) or row.get("role") not in ("system", "developer", "user", "assistant")
                    or not isinstance(row.get("content"), str) or set(row) != {"role", "content"}):
                raise ConfigurationError("Only role/content text messages are supported")
            clean.append(dict(row))
        payload = dict(model=self.config.model, messages=clean, stream=False,
                       **{self.config.max_tokens_parameter: max_tokens})
        if self.config.thinking_enabled is not None:
            payload["thinking"] = {"type": "enabled" if self.config.thinking_enabled else "disabled"}
        if self.config.reasoning_effort is not None:
            payload[self.config.reasoning_parameter] = ({"effort": self.config.reasoning_effort}
                if self.config.reasoning_parameter == "reasoning" else self.config.reasoning_effort)
        payload.update(json.loads(canonical(self.identity["extra_body"])))
        # Text-token upper bound: UTF-8 bytes plus generous framing allowance.
        # The caller must confirm provider token-limit and pricing semantics.
        input_bound = len(canonical(clean).encode()) + 1024 + 128 * len(clean)
        reserve = self.config.pricing.reserve(input_bound, max_tokens)
        return dict(payload=payload, input_token_bound=input_bound, max_output_tokens=max_tokens,
                    reserved_usd=str(reserve), request_sha256=fingerprint(payload))

    def chat(self, messages, max_tokens=32768, metadata=None):
        if self.config.endpoint_confirmed is not True:
            raise ConfigurationError("Endpoint/model configuration is unconfirmed; no request sent")
        if self.transport is None and self.allow_network is not True:
            raise ConfigurationError("Live network calls are disabled; no request sent")
        preview = self.preview(messages, max_tokens)
        metadata = {} if metadata is None else metadata
        if not isinstance(metadata, dict):
            raise ConfigurationError("Request metadata must be a JSON object")
        try:
            canonical(metadata)
        except (ValueError, TypeError):
            raise ConfigurationError("Request metadata is not finite JSON") from None
        key = read_credential(self.credentials_path, self.credential_index, endpoint_origin(self.config.endpoint))
        if key in canonical(preview["payload"]) or key in canonical(metadata):
            del key
            raise CredentialError("Credential content must not appear in prompts or metadata")
        upper = amount(preview["reserved_usd"])
        request_id = self.ledger.reserve(self.config.client_id, upper, request_metadata={
            "request_sha256": preview["request_sha256"], "input_token_bound": preview["input_token_bound"],
            "max_output_tokens": max_tokens, "metadata": metadata})
        folder = self.ledger.directory / "requests" / request_id
        # If writing fails before POST, the durable reservation remains held.
        atomic_json(folder / "request.json", dict(request_id=request_id, client_id=self.config.client_id,
                    endpoint=self.config.endpoint, payload=preview["payload"], metadata=metadata,
                    reserved_usd=str(upper), credential_index=self.credential_index))
        started = time.monotonic()
        try:
            response = (self.transport or _post_once)(endpoint=self.config.endpoint, payload=preview["payload"],
                                                       api_key=key, timeout=self.config.request_timeout_seconds)
        except Exception as error:
            fields = dict(error_type=type(error).__name__, elapsed_seconds=time.monotonic() - started)
            if isinstance(error, urllib.error.HTTPError):
                fields["http_status"] = error.code
            self.ledger.finish(request_id, state="unknown_charge", **fields)
            del key
            raise ClientError(f"Request failed; reservation retained; request_id={request_id}") from None
        # Only approved final-code and billing fields may be persisted below.
        if not isinstance(response, dict):
            self.ledger.finish(request_id, state="unknown_charge", error_type="invalid_response_type")
            del key
            raise ResponseError("Invalid provider response; reservation retained")
        returned_model = response.get("model")
        generation_id = response.get("id")
        returned_model = returned_model if isinstance(returned_model, str) and key not in returned_model else None
        generation_id = generation_id if isinstance(generation_id, str) and key not in generation_id else None
        model_ok = returned_model in self.identity["allowed_returned_models"]
        raw_usage = response.get("usage")
        raw_usage = raw_usage if isinstance(raw_usage, dict) else {}
        normalized_usage, estimated, actual, accounting_error = None, None, None, None
        try:
            estimated, normalized_usage = estimate_charge(raw_usage, self.config.pricing,
                completion_includes_reasoning=self.config.completion_tokens_include_reasoning)
        except ResponseError:
            accounting_error = "Missing or inconsistent token usage"
        if raw_usage.get("cost") is not None:
            try:
                actual = amount(raw_usage["cost"])
            except ConfigurationError:
                accounting_error = "Provider cost field is invalid"
                estimated = None
        state = "actual" if actual is not None else "pricing_upper_estimate" if estimated is not None and model_ok else "unknown_charge"
        effective = actual if actual is not None else estimated if state == "pricing_upper_estimate" else upper
        bounds_exceeded = effective > upper
        if normalized_usage:
            bounds_exceeded |= (normalized_usage["prompt_tokens"] > preview["input_token_bound"]
                                or normalized_usage["billed_output_tokens"] > max_tokens)
        pause_reason = ("Unexpected returned model" if not model_ok else "Request exceeded frozen token/price bounds" if bounds_exceeded else None)
        choices = response.get("choices")
        choice = choices[0] if isinstance(choices, list) and choices else None
        finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
        finish_reason = finish_reason if finish_reason in ("stop", "length", "content_filter", "tool_calls", "function_call") else None
        content, sources, parse_error = None, [], None
        try:
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            if not isinstance(message, dict) or message.get("tool_calls") or message.get("function_call"):
                raise ResponseError("Tool calls are unsupported in this code-only client")
            if finish_reason != "stop":
                raise ResponseError("Provider did not finish a complete code response")
            raw_content = message.get("content")
            if isinstance(raw_content, str) and key in raw_content:
                raise ResponseError("Response contains credential material and cannot be persisted")
            content, sources = extract_code_only(raw_content)
        except ResponseError as error:
            parse_error = str(error)
        del key
        info = dict(request_id=request_id, requested_model=self.config.model, returned_model=returned_model,
            generation_id=generation_id, cost_status=state, actual_cost_usd=float(actual) if actual is not None else None,
            estimated_upper_usd=float(estimated) if state == "pricing_upper_estimate" else None,
            reserved_usd=float(upper), usage=normalized_usage, finish_reason=finish_reason,
            elapsed_seconds=time.monotonic() - started, accounting_error=accounting_error,
            response_error=parse_error, model_matches=model_ok, bounds_exceeded=bool(bounds_exceeded),
            requested_thinking_enabled=self.config.thinking_enabled,
            requested_reasoning_effort=self.config.reasoning_effort,
            reasoning_parameter=self.config.reasoning_parameter, provider_reasoning_setting_verified=False,
            code_sha256=[hashlib.sha256(source.encode()).hexdigest() for source in sources])
        # Preserve a recoverable sanitized receipt before releasing reservation.
        # A crash before settlement remains conservative (pending still held).
        atomic_json(folder / "response.json", dict(info, content=content))
        self.ledger.finish(request_id, state=state, pause_reason=pause_reason,
            actual_cost_usd=str(actual) if actual is not None else None,
            estimated_upper_usd=str(estimated) if state == "pricing_upper_estimate" else None,
            returned_model=returned_model, generation_id=generation_id, usage=normalized_usage,
            elapsed_seconds=info["elapsed_seconds"], accounting_error=accounting_error, response_error=parse_error,
            model_matches=model_ok, bounds_exceeded=bool(bounds_exceeded))
        if pause_reason:
            raise ResponseError(pause_reason + f"; shared ledger paused; request_id={request_id}")
        if state == "unknown_charge":
            raise ResponseError(f"Cannot establish billed usage; reservation retained; request_id={request_id}")
        if parse_error:
            raise ResponseError(parse_error + f"; billed request preserved; request_id={request_id}")
        return content, info
