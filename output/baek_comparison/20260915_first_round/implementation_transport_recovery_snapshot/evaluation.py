"""Evaluate frozen artifacts in the OS sandbox, never in the parent process.

Source screening and repeated-state probes are conservative review aids, not a
proof of stationarity. The operating-system sandbox is the security boundary.
"""
from __future__ import annotations

import ast
import base64
import json
import math
from pathlib import Path
import zlib

import numpy as np

from .environment import Scenario


_RESULT_MARKER = "BAEK_EVALUATION_RESULT:"
_REVIEW_MODULES = {
    "inspect", "os", "sys", "pathlib", "socket", "requests", "urllib", "http",
    "subprocess", "multiprocessing", "threading", "ctypes", "importlib",
    "builtins", "pickle", "marshal", "types", "signal", "resource", "gc", "io",
}
_REVIEW_CALLS = {
    "open", "input", "exec", "eval", "compile", "__import__", "globals",
    "locals", "vars", "getattr", "setattr", "delattr", "breakpoint",
}
_REVIEW_ATTRIBUTES = {
    "load", "save", "loadtxt", "savetxt", "fromfile", "tofile", "memmap",
    "read_text", "read_bytes", "write_text", "write_bytes", "read_csv",
    "read_pickle", "read_json", "f_globals", "f_locals", "gi_frame", "cr_frame",
    "currentframe", "stack", "_getframe", "f_back", "f_code", "environ", "getenv", "system", "popen",
    "open_memmap", "genfromtxt", "fromregex", "loadmat", "savemat", "netcdf_file", "DataSource",
} | _REVIEW_CALLS


def review_source(code: str) -> dict:
    """Flag file/network/introspection access; ordinary setup timing is allowed."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"status": "invalid", "issues": [{"line": exc.lineno, "reason": "syntax_error", "detail": exc.msg}]}
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _REVIEW_MODULES:
                    issues.append({"line": node.lineno, "reason": "restricted_module", "detail": alias.name})
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] in _REVIEW_MODULES:
                issues.append({"line": node.lineno, "reason": "restricted_module", "detail": node.module})
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in _REVIEW_CALLS:
            issues.append({"line": node.lineno, "reason": "introspection_or_io", "detail": node.id})
        elif isinstance(node, ast.Attribute) and (
            node.attr.startswith("__") or node.attr in _REVIEW_ATTRIBUTES
        ):
            issues.append({"line": node.lineno, "reason": "introspection_or_io", "detail": node.attr})
    return {
        "status": "review_required" if issues else "passed",
        "issues": issues,
        "limitation": "Static screening and dynamic probes do not prove stationarity or prevent every Python introspection technique.",
    }


def numeric_design_params(scenario: Scenario) -> dict:
    """Exactly the numeric keys specified by the L2 prompt; no scenario ID."""
    params = {
        key: getattr(scenario, key)
        for key in ("lead_time", "mean_demand", "holding_cost", "lost_sales_cost", "horizon")
    }
    if scenario.distribution == "normal":
        params["std_normal"] = scenario.std_normal
    return params


# Trusted wrapper source. Policy source gets a separate global namespace that
# contains neither demand data nor worker globals. Files containing the wrapper
# are only inside the OS sandbox's ephemeral scratch directory.
_WORKER = r'''
import base64, contextlib, hashlib, json, math, signal, sys, time, types, zlib
import numpy as np

class EvaluationTimeout(TimeoutError):
    pass

class CallableReviewRequired(Exception):
    pass

class DiscardOutput:
    def write(self, text):
        return len(text)
    def flush(self):
        pass

stage = "setup"
def alarm_handler(_signal, _frame):
    raise EvaluationTimeout(stage + " timeout")
signal.signal(signal.SIGALRM, alarm_handler)

payload = json.loads(zlib.decompress(base64.b64decode(PAYLOAD)))
environment = types.ModuleType("_baek_eval_environment")
environment.__file__ = "/isolated/environment.py"
sys.modules[environment.__name__] = environment
exec(compile(ENVIRONMENT_SOURCE, "environment.py", "exec"), environment.__dict__)
scenario = environment.Scenario(**payload["scenario"])
response = {"status": "invalid", "batches": {}, "setup_seconds": None}
policy_globals = {"__name__": "submitted_policy"}
discard = DiscardOutput()

def valid_action(value):
    from numbers import Real
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError("Policy did not return a real scalar")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("Policy did not return a finite nonnegative action")
    return number

def guarded_policy(*, on_hand_inventory, pipeline_orders):
    global stage
    stage = "policy_action"
    signal.setitimer(signal.ITIMER_REAL, payload["action_timeout_seconds"])
    try:
        return policy(on_hand_inventory=on_hand_inventory, pipeline_orders=pipeline_orders)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

def fingerprint(value, seen=None):
    seen = set() if seen is None else seen
    if value is None or isinstance(value, (bool, int, float, str, np.generic)):
        return repr(value)
    if id(value) in seen:
        return ["cycle"]
    seen.add(id(value))
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            return ["object_array", fingerprint(value.tolist(), seen)]
        return ["array", str(value.dtype), list(value.shape), hashlib.sha256(value.tobytes()).hexdigest()]
    if isinstance(value, dict):
        return ["dict", sorted((str(k), fingerprint(v, seen.copy())) for k, v in value.items())]
    if isinstance(value, (tuple, list)):
        return [type(value).__name__, [fingerprint(v, seen.copy()) for v in value]]
    if isinstance(value, (set, frozenset)):
        return [type(value).__name__, sorted(str(fingerprint(v, seen.copy())) for v in value)]
    if isinstance(value, types.FunctionType):
        return ["function", value.__name__, [fingerprint(c.cell_contents, seen.copy()) for c in (value.__closure__ or ())]]
    if isinstance(value, (types.ModuleType, type, np.ufunc)):
        return ["fixed_symbol", type(value).__name__]
    # Objects such as interpolators cannot be exhaustively inspected here.
    return ["opaque", type(value).__module__, type(value).__name__]

def snapshot():
    values = {
        k: fingerprint(v) for k, v in policy_globals.items()
        if not k.startswith("__") and not isinstance(v, (types.ModuleType, type))
    }
    values["RETURNED_POLICY"] = fingerprint(policy)
    return json.dumps(values, sort_keys=True)

def action_dependencies(fn, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(fn, types.FunctionType) or id(fn) in seen:
        return []
    seen.add(id(fn))
    issues = []
    names = set(fn.__code__.co_names)
    referenced = [fn.__globals__[n] for n in names if n in fn.__globals__]
    referenced += [c.cell_contents for c in (fn.__closure__ or ())]
    for value in referenced:
        if isinstance(value, types.ModuleType) and value.__name__.split(".")[0] in {"time", "random"}:
            issues.append("Action references " + value.__name__)
        elif isinstance(value, types.FunctionType):
            if value.__module__ in {"time", "random"}:
                issues.append("Action references " + value.__module__)
            elif value.__globals__ is policy_globals:
                issues.extend(action_dependencies(value, seen))
        elif isinstance(value, (types.BuiltinFunctionType, types.BuiltinMethodType)) and getattr(value, "__module__", None) == "time":
            issues.append("Action references time")
        elif isinstance(value, (np.random.Generator, np.random.RandomState)):
            issues.append("Action captures mutable random generator")
    if "random" in names and any(isinstance(v, types.ModuleType) and v.__name__ == "numpy" for v in referenced):
        issues.append("Action accesses numpy.random")
    return issues

try:
    started = time.perf_counter()
    signal.setitimer(signal.ITIMER_REAL, payload["setup_timeout_seconds"])
    try:
        with contextlib.redirect_stdout(discard), contextlib.redirect_stderr(discard):
            exec(compile(payload["code"], "submitted_policy.py", "exec"), policy_globals)
            if payload["level"] == "L1":
                policy = policy_globals.get("compute_order_amount")
            else:
                design = policy_globals.get("design")
                if not callable(design):
                    raise TypeError("L2 source must define design(params)")
                policy = design(payload["design_params"].copy())
            if not callable(policy):
                raise TypeError("Submission must produce a callable policy")
            if not isinstance(policy, types.FunctionType):
                raise CallableReviewRequired(
                    "Callable objects require a separate stationarity audit before action execution"
                )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        response["setup_seconds"] = time.perf_counter() - started
        response["setup_exceeded_30_seconds"] = response["setup_seconds"] > 30

    dependencies = action_dependencies(policy)
    response["stationarity_check"] = {
        "proof": False,
        "limitation": "Repeated-state tests and mutation fingerprints can detect violations but cannot prove stationarity; opaque imported objects are not exhaustively inspected.",
        "action_dependency_issues": dependencies,
    }
    if dependencies:
        response["status"] = "review_required"
    else:
        stage = "stationarity_probe"
        signal.setitimer(signal.ITIMER_REAL, payload["action_timeout_seconds"])
        try:
            before = snapshot()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        mean = scenario.mean_demand
        length = scenario.lead_time - 1
        states = [
            (0.0, [0.0] * length),
            (mean, [mean] * length),
            (2.0 * mean, [0.0] * length),
            (0.5 * mean, [(j + 1) * 0.3 * mean for j in range(length)]),
        ]
        sequence = [0, 1, 2, 0, 3, 2, 1, 3, 0]
        observed = {}
        with contextlib.redirect_stdout(discard), contextlib.redirect_stderr(discard):
            for index in sequence:
                stock, pipeline = states[index]
                action = valid_action(guarded_policy(on_hand_inventory=stock, pipeline_orders=pipeline.copy()))
                if index in observed and action != observed[index]:
                    raise ValueError("Nonstationary/nondeterministic action at repeated identical state")
                observed[index] = action
        stage = "stationarity_probe"
        signal.setitimer(signal.ITIMER_REAL, payload["action_timeout_seconds"])
        try:
            changed = before != snapshot()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        response["stationarity_check"].update({"repeated_states_passed": True, "mutable_state_changed": changed, "n_probe_calls": len(sequence)})
        if changed:
            response["status"] = "review_required"
        else:
            response["status"] = "ok"
            for batch in payload["batches"]:
                response["active_batch"] = batch["name"]
                started = time.perf_counter()
                with contextlib.redirect_stdout(discard), contextlib.redirect_stderr(discard):
                    result = environment.simulate_policy(
                        guarded_policy, scenario, np.asarray(batch["demands"], dtype=float),
                        mode=batch["mode"], burn_in=batch["burn_in"], integer_orders=batch["integer_orders"],
                    )
                arrays = {key: getattr(result, key).tolist() for key in (
                    "total_cost", "holding_cost", "lost_sales_cost", "demand_units",
                    "sales_units", "lost_units", "service_level", "policy_seconds",
                )}
                response["batches"][batch["name"]] = {
                    "summary": result.summary(), "per_path": arrays,
                    "evaluation_seconds": time.perf_counter() - started,
                    "mean_action_seconds": float(result.policy_seconds.sum() / (len(result.total_cost) * result.periods_simulated)),
                }
                stage = "stationarity_after_evaluation"
                signal.setitimer(signal.ITIMER_REAL, payload["action_timeout_seconds"])
                try:
                    changed = before != snapshot()
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                if changed:
                    response["stationarity_check"]["mutable_state_changed"] = True
                    response["status"] = "review_required"
                    break
            response.pop("active_batch", None)
except Exception as exc:
    response["status"] = (
        "review_required" if isinstance(exc, CallableReviewRequired)
        else "timeout" if isinstance(exc, EvaluationTimeout) or isinstance(exc.__cause__, EvaluationTimeout)
        else "invalid"
    )
    response["error"] = {"type": type(exc).__name__, "message": str(exc)[:2000], "stage": stage}
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
encoded = base64.b64encode(zlib.compress(json.dumps(response, allow_nan=False).encode(), 6)).decode()
print(RESULT_MARKER + encoded)
'''


def evaluate_artifact_batches(
    code: str,
    level: str,
    scenario: Scenario,
    batches: list[dict],
    sandbox,
    *,
    timeout_seconds: float = 1200,
    setup_timeout_seconds: float = 600,
    action_timeout_seconds: float = 1,
) -> dict:
    """Construct once, then evaluate named demand batches in one sandbox worker.

    Each batch has name, demands, and optional mode/burn_in/integer_orders.
    Review-required artifacts are returned explicitly and are not scored.
    All timeout/failure outcomes remain failures, never substitute zero actions.
    """
    if level not in {"L1", "L2"}:
        raise ValueError("level must be L1 or L2")
    for key, value in (("timeout_seconds", timeout_seconds), ("setup_timeout_seconds", setup_timeout_seconds), ("action_timeout_seconds", action_timeout_seconds)):
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(key + " must be finite and positive")
    if setup_timeout_seconds > 600:
        raise ValueError("Initialization guard cannot exceed 600 seconds")
    review = review_source(code)
    if review["status"] != "passed":
        return {"status": review["status"], "source_review": review, "batches": {}, "setup_seconds": None}
    names = set()
    normalized = []
    for batch in batches:
        name = batch["name"]
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Batch names must be unique nonempty strings")
        names.add(name)
        demands = np.asarray(batch["demands"])
        if np.iscomplexobj(demands):
            raise ValueError("Demand arrays must be real")
        demands = np.asarray(demands, dtype=float)
        if not np.isfinite(demands).all() or (demands < 0).any():
            raise ValueError("Demand arrays must be finite and nonnegative")
        normalized.append({
            "name": name, "demands": demands.tolist(), "mode": batch.get("mode", "finite"),
            "burn_in": batch.get("burn_in", 0), "integer_orders": batch.get("integer_orders", False),
        })
    if not normalized:
        raise ValueError("At least one evaluation batch is required")
    payload = {
        "code": code, "level": level, "scenario": scenario.to_params(),
        "design_params": numeric_design_params(scenario), "batches": normalized,
        "setup_timeout_seconds": min(setup_timeout_seconds, timeout_seconds),
        "action_timeout_seconds": action_timeout_seconds,
    }
    encoded = base64.b64encode(zlib.compress(json.dumps(payload, allow_nan=False).encode(), 6)).decode()
    environment_source = Path(__file__).with_name("environment.py").read_text(encoding="utf-8")
    worker = (
        "PAYLOAD = " + repr(encoded) + "\nENVIRONMENT_SOURCE = " + repr(environment_source)
        + "\nRESULT_MARKER = " + repr(_RESULT_MARKER) + "\n" + _WORKER
    )
    result = sandbox.run(worker, timeout_seconds=timeout_seconds, max_output_bytes=16 * 1024 * 1024)
    worker_info = {
        "elapsed_seconds": result.elapsed_seconds, "returncode": result.returncode,
        "timed_out": result.timed_out,
    }
    if result.timed_out or result.returncode != 0:
        return {
            "status": "timeout" if result.timed_out else "worker_failed", "source_review": review,
            "worker": worker_info, "batches": {}, "setup_seconds": None,
            "error": {"message": result.stderr[-2000:]},
        }
    markers = [line.removeprefix(_RESULT_MARKER) for line in result.stdout.splitlines() if line.startswith(_RESULT_MARKER)]
    if len(markers) != 1:
        return {"status": "worker_failed", "source_review": review, "worker": worker_info, "batches": {}, "setup_seconds": None, "error": {"message": "Missing or ambiguous worker result"}}
    try:
        response = json.loads(zlib.decompress(base64.b64decode(markers[0], validate=True)))
    except (ValueError, zlib.error) as exc:
        return {"status": "worker_failed", "source_review": review, "worker": worker_info, "batches": {}, "setup_seconds": None, "error": {"message": "Invalid worker result: " + type(exc).__name__}}
    response["source_review"] = review
    response["worker"] = worker_info
    return response


def evaluate_artifact(
    code: str,
    level: str,
    scenario: Scenario,
    demands,
    sandbox,
    *,
    mode: str = "finite",
    burn_in: int = 0,
    integer_orders: bool = False,
    timeout_seconds: float = 1200,
    setup_timeout_seconds: float = 600,
    action_timeout_seconds: float = 1,
) -> dict:
    """Convenience wrapper exposing summary and per_path for one batch."""
    response = evaluate_artifact_batches(
        code, level, scenario,
        [{"name": "evaluation", "demands": demands, "mode": mode, "burn_in": burn_in, "integer_orders": integer_orders}],
        sandbox, timeout_seconds=timeout_seconds, setup_timeout_seconds=setup_timeout_seconds,
        action_timeout_seconds=action_timeout_seconds,
    )
    if "evaluation" in response.get("batches", {}):
        response.update(response["batches"]["evaluation"])
    return response
