"""Killable OS-isolated policy evaluation with structure-cached Numba compilation.

Only caller-supplied tapes enter the worker. Parameter substitution changes a
runtime vector, not the compiled program. No model credentials enter the child.
"""
from __future__ import annotations

import ast
import base64
import contextlib
import hashlib
import inspect
import io
import json
import math
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time
import zlib

import numpy as np


ARGUMENTS = ("on_hand_inventory", "pipeline_orders", "last_demand", "quoted_lead_time")
SAFE_BUILTINS = {"abs", "min", "max", "sum", "len", "range", "float", "int", "round", "enumerate"}
SAFE_MATH = {"sqrt", "exp", "expm1", "log", "log1p", "log2", "log10", "fabs", "floor", "ceil",
             "erf", "erfc", "tanh", "isfinite", "pow", "sin", "cos", "atan", "pi", "e", "inf"}
SAFE_NUMPY = {"sum", "mean", "std", "var", "min", "max", "minimum", "maximum", "clip", "sqrt",
              "exp", "expm1", "log", "log1p", "tanh", "abs", "floor", "ceil", "isfinite",
              "dot", "quantile", "percentile", "median", "array", "asarray", "zeros", "ones",
              "float64", "int64", "arange", "linspace", "pi", "inf"}


def parameterized_kernel_source():
    """Derive the theta-aware kernel mechanically from the single event kernel."""
    from .environment import simulate_kernel
    tree = ast.parse(inspect.getsource(simulate_kernel))
    fn = tree.body[0]
    fn.name = "simulate_kernel_parameterized"
    fn.args.args.append(ast.arg(arg="theta"))
    fn.args.defaults.append(ast.Constant(value=None))
    calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "policy"]
    if len(calls) != 1:
        raise ValueError("Expected exactly one policy call in trusted kernel")
    calls[0].args.append(ast.Name(id="theta", ctx=ast.Load()))
    return ast.unparse(ast.fix_missing_locations(tree))


def prepare_policy(code: str, max_opt_params: int = 4):
    """Validate the numerical policy subset and remove parameter values from AST."""
    if not isinstance(code, str) or len(code.encode()) > 100_000:
        raise ValueError("Policy source must be at most 100 KB")
    tree = ast.parse(code)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if len(functions) != 1 or functions[0].name != "compute_order_amount":
        raise ValueError("Provide exactly one compute_order_amount function")
    fn = functions[0]
    if (tuple(a.arg for a in fn.args.args) != ARGUMENTS or fn.args.posonlyargs or fn.args.kwonlyargs
            or fn.args.vararg or fn.args.kwarg or fn.args.defaults or fn.decorator_list):
        raise ValueError("Policy signature must contain exactly the four plain positional arguments")
    modules, direct_math = {}, set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in {"math", "numpy"}:
                    raise ValueError("Only math and numpy imports are allowed")
                modules[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module != "math" or node.level or any(a.name not in SAFE_MATH for a in node.names):
                raise ValueError("Only whitelisted math imports are allowed")
            direct_math.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Assign):
            # Module constants must be immutable literals, never mutable state.
            value = ast.literal_eval(node.value)
            def immutable(v):
                return ((isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v))
                        or (isinstance(v, tuple) and all(immutable(x) for x in v)))
            if not immutable(value) or any(not isinstance(t, ast.Name) for t in node.targets):
                raise ValueError("Module assignments must be immutable numerical literals")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            pass
        elif node is not fn:
            raise ValueError("Unsupported top-level policy statement")
    prohibited = (ast.ClassDef, ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom, ast.Global,
                  ast.Nonlocal, ast.With, ast.AsyncWith, ast.Try, ast.Raise, ast.Delete, ast.While,
                  ast.Lambda, ast.NamedExpr)
    for node in ast.walk(tree):
        if isinstance(node, prohibited):
            raise ValueError("Unsupported stateful or dynamic policy construct")
        if isinstance(node, ast.FunctionDef) and node is not fn:
            raise ValueError("Nested or helper functions are not permitted")
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in tree.body:
            raise ValueError("Imports must be at module scope")
        if isinstance(node, ast.Name) and (node.id.startswith("__") or node.id == "_opt_values"):
            raise ValueError("Reserved name in policy")
        if isinstance(node, ast.Attribute):
            if (isinstance(node.ctx, (ast.Store, ast.Del))
                    or not isinstance(node.value, ast.Name) or node.value.id not in modules
                    or node.attr not in (SAFE_MATH if modules[node.value.id] == "math" else SAFE_NUMPY)):
                raise ValueError("Only whitelisted numerical module attributes are allowed")
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            raise ValueError("Array or input mutation is not allowed")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id not in SAFE_BUILTINS | direct_math:
                raise ValueError("Unsupported function call: " + node.func.id)
        if isinstance(node, ast.Call) and not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise ValueError("Dynamic call targets are not allowed")
        if isinstance(node, ast.Call) and any(k.arg is None or k.arg == 'out' for k in node.keywords):
            raise ValueError("Mutating outputs and expanded dynamic keyword arguments are forbidden")
        if isinstance(node, ast.AugAssign):
            raise ValueError("Use ordinary scalar assignments; in-place array mutation is forbidden")
    assignments = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            assignments.setdefault(node.lineno, []).append(node)
    configs, values, lines = {}, [], {}
    for number, line in enumerate(code.splitlines(), 1):
        if "OPT_PARAM:" not in line:
            continue
        matching = assignments.get(number, [])
        if len(matching) != 1:
            raise ValueError("OPT_PARAM requires exactly one assignment on its source line")
        node = matching[0]
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise ValueError("OPT_PARAM must annotate a simple assignment inside the policy")
        name = node.targets[0].id
        if name in ARGUMENTS or name in configs:
            raise ValueError("Duplicate or input OPT_PARAM")
        config = ast.literal_eval(line.split("OPT_PARAM:", 1)[1].strip())
        value = ast.literal_eval(node.value)
        if (not isinstance(config, dict) or config.get("type") not in {"float", "int"}
                or any(k not in config for k in ("initial", "min", "max"))):
            raise ValueError("Invalid OPT_PARAM schema")
        numbers = [value, config["initial"], config["min"], config["max"]]
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in numbers):
            raise ValueError("OPT_PARAM numbers must be finite")
        if not config["min"] <= value <= config["max"] or config["min"] >= config["max"]:
            raise ValueError("OPT_PARAM value must lie within nondegenerate bounds")
        if config["type"] == "int" and value != int(value):
            raise ValueError("Integer OPT_PARAM must have an integer value")
        configs[name], lines[number] = dict(config), (len(values), config["type"])
        values.append(float(value))
    if len(configs) > max_opt_params:
        raise ValueError("Too many OPT_PARAM declarations")
    class ParameterTransformer(ast.NodeTransformer):
        def visit_Assign(self, node):
            if node.lineno in lines:
                index, kind = lines[node.lineno]
                replacement = ast.Subscript(value=ast.Name(id="_opt_values", ctx=ast.Load()),
                                            slice=ast.Constant(index), ctx=ast.Load())
                if kind == "int":
                    replacement = ast.Call(func=ast.Name(id="int", ctx=ast.Load()), args=[replacement], keywords=[])
                node.value = replacement
            return node
    tree = ParameterTransformer().visit(tree)
    fn.args.args.append(ast.arg(arg="_opt_values"))
    for arg in fn.args.args:
        arg.annotation = None
    fn.returns = None
    source = ast.unparse(ast.fix_missing_locations(tree))
    key = hashlib.sha256(source.encode()).hexdigest()
    return {"structure_sha256": key, "source": source, "values": values, "opt_params": configs,
            "code_sha256": hashlib.sha256(code.encode()).hexdigest()}


def _encode(value):
    return base64.b64encode(zlib.compress(json.dumps(value, allow_nan=False).encode(), 3)).decode()


def _decode(value):
    return json.loads(zlib.decompress(base64.b64decode(value)))


def _worker_main():
    from numba import njit
    root = Path(__file__).parent
    config = json.loads((root / "config.json").read_text())
    data = np.load(root / "tapes.npz", allow_pickle=False)
    demands, leads, initial = (data[name] for name in ("demands", "lead_times", "initial_last_demand"))
    namespace = {"np": np, "math": math}
    exec(compile(config["kernel_source"], "trusted_inventory_kernel.py", "exec"), namespace)
    kernel = njit(namespace["simulate_kernel_parameterized"], cache=False)
    cache, compilation_count = {}, 0
    n = len(demands)
    boot = np.random.default_rng(271828).integers(0, n, size=(1000, n))
    def respond(answer):
        print(_encode(answer), flush=True)
    respond({"status": "ready", "pid": os.getpid()})
    for raw in sys.stdin:
        try:
            request = json.loads(raw)
            if request.get("op") == "close":
                break
            prepared = prepare_policy(request["code"], config["max_opt_params"])
            key = prepared["structure_sha256"]
            compiled_new = key not in cache
            started = time.monotonic()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                if compiled_new:
                    policy_namespace = {}
                    exec(compile(prepared["source"], "candidate_policy.py", "exec"), policy_namespace)
                    pure = policy_namespace["compute_order_amount"]
                    compiled = njit(pure, cache=False)
                    theta = np.asarray(prepared["values"], dtype=np.float64)
                    # Compare original signature execution with transformed compiled execution on public states.
                    original_namespace = {}
                    exec(compile(request["code"], "original_candidate_policy.py", "exec"), original_namespace)
                    original = original_namespace["compute_order_amount"]
                    for inventory in (0., 75., 300.):
                        for quote in config["lead_values"]:
                            pipeline = np.arange(1, config["max_lead_time"], dtype=np.float64) * 17.
                            before = pipeline.copy()
                            expected = original(inventory, pipeline, 123., int(quote))
                            observed = compiled(inventory, pipeline.copy(), 123., int(quote), theta)
                            if (isinstance(expected, (bool, np.bool_)) or not np.isscalar(expected)
                                    or not math.isfinite(expected) or expected < 0
                                    or not np.array_equal(before, pipeline)
                                    or not math.isclose(float(expected), float(observed), rel_tol=1e-10, abs_tol=1e-9)):
                                raise ValueError("Original/compiled action contract mismatch")
                    cache[key] = compiled
                    compilation_count += 1
                theta = np.asarray(prepared["values"], dtype=np.float64)
                need_trace = request.get("windows") is not None or not request.get("compact", False)
                result = kernel(cache[key], demands, leads, initial, config["max_lead_time"],
                                config["holding_cost"], config["lost_sales_cost"], config["horizon"],
                                config["burnin"], need_trace, theta)
            holds, shortage, demand_total, sales_total, lost_total, trace = result
            answer = {"status": "ok", "code_sha256": prepared["code_sha256"], "structure_sha256": key,
                      "compiled_new": compiled_new, "compilation_count": compilation_count,
                      "evaluation_seconds": time.monotonic()-started, "opt_params": prepared["opt_params"]}
            if request.get("windows") is not None:
                windows = []
                for burnin, horizon in request["windows"]:
                    if not (isinstance(burnin, int) and isinstance(horizon, int) and burnin >= 0
                            and horizon > 0 and burnin+horizon <= trace.shape[1]):
                        raise ValueError("Invalid evaluation window")
                    cut = trace[:, burnin:burnin+horizon]
                    h = cut[:, :, 8].sum(axis=1)*config["holding_cost"]
                    p = cut[:, :, 7].sum(axis=1)*config["lost_sales_cost"]
                    windows.append({"burnin": burnin, "horizon": horizon,
                                    "total_cost": (h+p).tolist(), "holding_cost": h.tolist(),
                                    "lost_sales_cost": p.tolist(), "demand_units": cut[:, :, 5].sum(axis=1).tolist(),
                                    "sales_units": cut[:, :, 6].sum(axis=1).tolist(),
                                    "lost_units": cut[:, :, 7].sum(axis=1).tolist(),
                                    "order_units": cut[:, :, 4].sum(axis=1).tolist(),
                                    "mean_cost_per_period": float((h+p).mean()/horizon)})
                answer["windows"] = windows
            else:
                total = holds+shortage
                ci = np.percentile(total[boot].mean(axis=1), [2.5, 97.5])
                answer.update(avg=float(total.mean()), lower=float(ci[0]), upper=float(ci[1]),
                              trajectory=total.tolist(), order_matrix=[], cost_matrix=[])
                if need_trace:
                    scored = trace[:, config["burnin"]:]
                    answer.update(order_matrix=scored[:, :, 4].tolist(),
                                  cost_matrix=np.stack((scored[:, :, 8]*config["holding_cost"],
                                                        scored[:, :, 7]*config["lost_sales_cost"]), axis=2).tolist())
            respond(answer)
        except Exception as exc:
            respond({"status": "invalid", "error": type(exc).__name__+": "+str(exc)[:3000]})


class FastPolicyWorker:
    """A persistent, isolated evaluator; close() kills the process group."""
    def __init__(self, tapes, scenario, *, burnin=500, horizon=200, python_executable=None,
                 timeout=180., max_opt_params=4):
        from .data import validate_tapes
        from ..baek_comparison.sandbox import PythonSandbox
        normalized = validate_tapes(tapes, scenario)
        if isinstance(burnin, bool) or isinstance(horizon, bool) or burnin < 0 or horizon < 1:
            raise ValueError("Invalid window")
        periods = int(burnin+horizon)
        if periods > normalized["demands"].shape[1]:
            raise ValueError("Training tape is too short")
        self.timeout, self._lock, self._buffer = float(timeout), threading.Lock(), b""
        self._tmp = tempfile.TemporaryDirectory(prefix="correlated-policy-")
        scratch = Path(self._tmp.name).resolve()
        self._sandbox = PythonSandbox(python_executable or sys.executable)
        # Grant only the numerical compiler runtime, never the repository or all site-packages.
        probe = subprocess.run([self._sandbox.python_executable, "-I", "-B", "-c",
                                "import json,importlib.util; print(json.dumps({n:importlib.util.find_spec(n).origin "
                                "for n in ['numba','llvmlite','packaging'] if importlib.util.find_spec(n)}))"],
                               capture_output=True, text=True, timeout=30, check=True)
        extra = json.loads(probe.stdout)
        profile = self._sandbox._profile(scratch)
        for path in extra.values():
            package = Path(path).resolve().parent
            profile += "\n(allow file-read* (subpath " + json.dumps(str(package)) + "))"
            for dist in package.parent.glob(package.name+"*.dist-info"):
                profile += "\n(allow file-read* (subpath " + json.dumps(str(dist)) + "))"
        (scratch / "sandbox.sb").write_text(profile)
        (scratch / "fast_policy.py").write_bytes(Path(__file__).read_bytes())
        np.savez(scratch / "tapes.npz", **{key: normalized[key][:, :periods]
                 if normalized[key].ndim == 2 else normalized[key]
                 for key in ("demands", "lead_times", "initial_last_demand")})
        config = dict(burnin=int(burnin), horizon=int(horizon), max_opt_params=int(max_opt_params),
                      max_lead_time=scenario.max_lead_time, lead_values=list(scenario.lead_time_values),
                      holding_cost=scenario.holding_cost, lost_sales_cost=scenario.lost_sales_cost,
                      kernel_source=parameterized_kernel_source())
        (scratch / "config.json").write_text(json.dumps(config, allow_nan=False))
        siteparents = sorted({str(Path(self._sandbox.runtime[n]).resolve().parent.parent) for n in ("numpy", "scipy")}
                             | {str(Path(p).resolve().parent.parent) for p in extra.values()})
        stdlib = Path(self._sandbox.runtime["stdlib"]).resolve()
        (scratch / "bootstrap.py").write_text(
            "import sys,resource\n"
            + "sys.path[:]= "+repr([str(scratch), str(stdlib), str(stdlib/'lib-dynload')]+siteparents)+"\n"
            + "resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))\n"
            + "resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))\n"
            + "import fast_policy\nfast_policy._worker_main()\n")
        env = {"HOME": str(scratch), "TMPDIR": str(scratch), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
               "LC_ALL": "C.UTF-8", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
               "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1", "NUMBA_NUM_THREADS": "1",
               "NUMBA_CACHE_DIR": str(scratch/'numba-cache')}
        self._error_file = (scratch/'stderr').open('wb')
        self._proc = subprocess.Popen([self._sandbox.sandbox_exec, "-f", str(scratch/'sandbox.sb'),
                                       self._sandbox._runner, "-I", "-B", "-S", str(scratch/'bootstrap.py')],
                                      cwd=scratch, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=self._error_file, start_new_session=True)
        try:
            if self._read_response()["status"] != "ready":
                raise RuntimeError("Sandbox evaluator did not initialize")
        except BaseException:
            self.close()
            raise

    def _read_response(self):
        deadline = time.monotonic()+self.timeout
        while b"\n" not in self._buffer:
            if self._proc.poll() is not None:
                error = (Path(self._tmp.name)/'stderr').read_text(errors='replace')[-4000:]
                raise RuntimeError("Sandbox evaluator exited: "+error)
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                self.close()
                raise TimeoutError("Sandbox policy evaluation timed out")
            ready, _, _ = select.select([self._proc.stdout], [], [], min(remaining, 1.))
            if ready:
                chunk = os.read(self._proc.stdout.fileno(), 65536)
                if not chunk:
                    continue
                self._buffer += chunk
                if len(self._buffer) > 16*1024*1024:
                    self.close()
                    raise RuntimeError("Worker response exceeded 16 MiB")
        line, self._buffer = self._buffer.split(b"\n", 1)
        return _decode(line)

    def _request(self, code, windows=None, compact=False):
        with self._lock:
            if self._proc.poll() is not None:
                raise RuntimeError("Policy worker is closed")
            message = json.dumps({"code": code, "windows": windows, "compact": bool(compact)}, allow_nan=False).encode()+b"\n"
            self._proc.stdin.write(message)
            self._proc.stdin.flush()
            answer = self._read_response()
            if answer.get("status") != "ok":
                raise ValueError(answer.get("error", "Invalid policy"))
            return answer

    def evaluate(self, code, *, compact=False):
        return self._request(code, compact=compact)

    def evaluate_windows(self, code, windows):
        return self._request(code, [[int(b), int(h)] for b, h in windows])

    def close(self):
        process = getattr(self, "_proc", None)
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        if getattr(self, "_error_file", None):
            self._error_file.close()
        if getattr(self, "_tmp", None):
            self._tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
