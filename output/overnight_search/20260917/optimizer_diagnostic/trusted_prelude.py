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


def prepare_policy(code: str, max_opt_params: int | None = None):
    """Validate the numerical policy subset and remove parameter values from AST."""
    if not isinstance(code, str) or len(code.encode()) > 100_000:
        raise ValueError("Policy source must be at most 100 KB")
    tree, import_normalization = normalize_leading_policy_imports(ast.parse(code))
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
        if False:
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
    if max_opt_params is not None and len(configs) > max_opt_params:
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
            "code_sha256": hashlib.sha256(code.encode()).hexdigest(), "import_normalization": import_normalization}


"""Neutral import placement correction; submitted source text stays unchanged."""
import ast


IMPORT_NORMALIZATION_REVISION = "leading_numerical_imports_v1"


def normalize_leading_policy_imports(tree):
    """Hoist leading numerical imports, preserving every original AST line.

    OPT_PARAM extraction still reads the original source and original assignment
    line numbers. Conditional/nonleading imports and other modules remain subject
    to the unchanged validator. Ambiguous rebinding is not normalized.
    """
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if len(functions) != 1 or functions[0].name != "compute_order_amount":
        return tree, []
    fn = functions[0]
    start = int(bool(fn.body and isinstance(fn.body[0], ast.Expr)
                     and isinstance(fn.body[0].value, ast.Constant)
                     and isinstance(fn.body[0].value.value, str)))
    imports = []
    for node in fn.body[start:]:
        allowed = (isinstance(node, ast.Import)
                   and all(alias.name in {"math", "numpy"} for alias in node.names))
        allowed = allowed or (isinstance(node, ast.ImportFrom)
                              and node.module == "math" and node.level == 0)
        if not allowed:
            break
        imports.append(node)
    if not imports:
        return tree, []
    bound = {alias.asname or alias.name for node in imports for alias in node.names}
    arguments = {arg.arg for arg in (fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs)}
    if fn.args.vararg:
        arguments.add(fn.args.vararg.arg)
    if fn.args.kwarg:
        arguments.add(fn.args.kwarg.arg)
    remainder = fn.body[start + len(imports):]
    # Moving an import must not expose an unbound local or change an argument.
    local_bindings = {node.id for statement in remainder for node in ast.walk(statement)
                      if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))}
    local_bindings.update(alias.asname or alias.name
                          for statement in remainder for node in ast.walk(statement)
                          if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names)
    following = tree.body[tree.body.index(fn) + 1:]
    later_bindings = {node.id for statement in following for node in ast.walk(statement)
                      if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))}
    later_bindings.update(alias.asname or alias.name
                         for statement in following for node in ast.walk(statement)
                         if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names)
    if bound & (arguments | local_bindings | later_bindings | {fn.name}):
        return tree, []
    metadata = [dict(revision=IMPORT_NORMALIZATION_REVISION, action="hoist_leading_import",
                     original_line=node.lineno, original_end_line=node.end_lineno,
                     import_statement=ast.unparse(node)) for node in imports]
    fn.body[start:start + len(imports)] = []
    if not fn.body:
        fn.body = [ast.copy_location(ast.Pass(), imports[-1])]
    position = tree.body.index(fn)
    tree.body[position:position] = imports
    return tree, metadata

ARGUMENTS = ("age", "pipeline", "mu", "cv", "f", "L")
"""Perishable-inventory screening model, with explicit source discrepancies.

Policy state is quantities by remaining life (oldest first) after receipt and
orders due in 1,...,L-1 periods. See docs/overnight_perishable_spec.md.
No API calls occur in this module.
"""


from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Callable

import numpy as np
from numba import njit
from scipy import stats


@dataclass(frozen=True)
class Scenario:
    name: str
    m: int
    L: int
    cv: float
    f: float
    mean: float = 4.0
    h: float = 0.0
    p: float = 100.0
    w: float = 100.0
    demand_mode: str = "paper_cv"
    cap_mode: str = "paper"

    @property
    def sd(self) -> float:
        if self.demand_mode == "paper_cv":
            return self.cv * self.mean
        if self.demand_mode == "legacy_code":
            return self.cv * np.sqrt(self.mean)
        raise ValueError(f"Unknown demand mode: {self.demand_mode}")

    def to_dict(self) -> dict:
        return {**asdict(self), "actual_cv": self.sd / self.mean,
                "inventory_cap": inventory_cap(self)}


def scenarios(demand_mode: str = "paper_cv", cap_mode: str = "paper") -> list[Scenario]:
    """The 12-instance factorial specified in the user's research advice."""
    return [Scenario(f"perish_m{m}_L2_cv{cv:g}_f{f:g}", m, 2, cv, f,
                     demand_mode=demand_mode, cap_mode=cap_mode)
            for m in (3, 4, 5) for cv in (1.5, 2.0) for f in (0.0, 0.5)]


def _aer_components(mean: float, sd: float):
    """Adan--van Eenige--Resing two-moment fit, matching DynaPlex formulas.

    Returns (mixture weight, scipy discrete distribution) pairs. These are
    untruncated laws; only the numerical PMF used to calculate caps is cut off.
    """
    if mean == 0:
        return [(1.0, None)]
    if mean < 0 or sd < 0:
        raise ValueError("Mean and SD must be nonnegative")
    fractional = mean - np.floor(mean)
    if sd * sd < fractional * (1 - fractional) - 1e-10:
        raise ValueError("These moments cannot define an integer-valued law")
    a = (sd / mean) ** 2 - 1 / mean
    if abs(a) < 1e-6:
        return [(1.0, stats.poisson(mean))]
    if a < 0:
        if abs(a + 1) < 1e-10:
            # Degenerate/Bernoulli endpoint is easier to represent directly.
            return [(1.0, stats.binom(1, mean))]
        k = int(np.floor(1 / -a))
        q = (1 + a * (1 + k) + np.sqrt(max(0, -a * k * (1 + k) - k))) / (1 + a)
        probability = mean / (k + 1 - q)
        return [(float(np.clip(q, 0, 1)), stats.binom(k, probability)),
                (float(np.clip(1 - q, 0, 1)), stats.binom(k + 1, probability))]
    if a < 1:
        k = int(np.floor(1 / a))
        q = ((1 + k) * a - np.sqrt(max(0, (1 + k) * (1 - a * k)))) / (1 + a)
        failure = mean / (k + 1 - q + mean)
        return [(float(np.clip(q, 0, 1)), stats.nbinom(k, 1 - failure)),
                (float(np.clip(1 - q, 0, 1)), stats.nbinom(k + 1, 1 - failure))]
    positive = 1 + a + np.sqrt(a * a - 1)
    negative = 1 + a - np.sqrt(a * a - 1)
    weight = 1 / positive
    # nbinom(1,p) is the geometric law on {0,1,...}.
    return [(weight, stats.nbinom(1, 2 / (2 + mean * positive))),
            (1 - weight, stats.nbinom(1, 2 / (2 + mean * negative)))]


@lru_cache(maxsize=128)
def aer_pmf(mean: float, sd: float, tail: float = 1e-13) -> np.ndarray:
    """PMF with a numerically negligible tail removed and then normalized."""
    components = _aer_components(mean, sd)
    if components[0][1] is None:
        return np.array([1.0])
    maximum = max(int(dist.isf(tail)) for weight, dist in components if weight > 0)
    support = np.arange(maximum + 1)
    pmf = sum(weight * dist.pmf(support) for weight, dist in components)
    pmf /= pmf.sum()
    return pmf


def sample_demands(scenario: Scenario, npaths: int, periods: int, seed: int) -> np.ndarray:
    """Independent FIFO and LIFO streams; last axis is [FIFO, LIFO].

    Group means are f*mu and (1-f)*mu, with variances f*SD^2 and
    (1-f)*SD^2. A binomial splitting of one total draw is a different model.
    """
    rng = np.random.default_rng(seed)
    shape = (npaths, periods)
    demands = np.zeros((*shape, 2), dtype=np.int64)
    for channel, fraction in enumerate((scenario.f, 1 - scenario.f)):
        components = _aer_components(fraction * scenario.mean,
                                     np.sqrt(fraction) * scenario.sd)
        if components[0][1] is None:
            continue
        if len(components) == 1:
            demands[:, :, channel] = components[0][1].rvs(size=shape, random_state=rng)
        else:
            choose_first = rng.random(shape) < components[0][0]
            first = components[0][1].rvs(size=shape, random_state=rng)
            second = components[1][1].rvs(size=shape, random_state=rng)
            demands[:, :, channel] = np.where(choose_first, first, second)
    return demands


@lru_cache(maxsize=128)
def inventory_cap(scenario: Scenario) -> int:
    """Newsvendor fractile of demand over m+L (paper) or m+L+1 (code)."""
    if scenario.cap_mode == "none":
        return -1
    if scenario.cap_mode not in ("paper", "legacy_code"):
        raise ValueError(f"Unknown cap mode: {scenario.cap_mode}")
    fifo = aer_pmf(scenario.f * scenario.mean, np.sqrt(scenario.f) * scenario.sd)
    lifo = aer_pmf((1 - scenario.f) * scenario.mean, np.sqrt(1 - scenario.f) * scenario.sd)
    daily = np.convolve(fifo, lifo)
    periods = scenario.m + scenario.L + int(scenario.cap_mode == "legacy_code")
    total = np.array([1.0])
    for _ in range(periods):
        total = np.convolve(total, daily)
    return int(np.searchsorted(np.cumsum(total), scenario.p / (scenario.p + scenario.w)))


@njit(cache=True)
def transition_inplace(age, pipeline, order, fifo, lifo, L):
    """Serve FIFO then LIFO; expire oldest; age; receive next-period stock.

    Returns (wasted units, lost units, held surviving units). Assumes feasible
    integer order. Both state arrays are updated to the next decision epoch.
    """
    m = len(age)
    if L == 0:
        age[m - 1] += order
    remaining_fifo = fifo
    for j in range(m):
        sold = min(age[j], remaining_fifo)
        age[j] -= sold
        remaining_fifo -= sold
    remaining_lifo = lifo
    for j in range(m - 1, -1, -1):
        sold = min(age[j], remaining_lifo)
        age[j] -= sold
        remaining_lifo -= sold
    wasted = age[0]
    held = age.sum() - wasted
    for j in range(m - 1):
        age[j] = age[j + 1]
    age[m - 1] = 0
    if L == 1:
        age[m - 1] = order
    elif L > 1:
        age[m - 1] = pipeline[0]
        for j in range(len(pipeline) - 1):
            pipeline[j] = pipeline[j + 1]
        pipeline[len(pipeline) - 1] = order
    return wasted, remaining_fifo + remaining_lifo, held


@njit(cache=True)
def evaluate_kernel(policy, theta, demands, m, L, cap, mu, cv, f, h, p, w, burnin):
    """Fast shared evaluator. `policy` must be a Numba dispatcher.

    policy(age,pipeline,theta,mu,cv,f,L)->scalar. Half-even integer rounding
    and clipping to the inventory-position cap are shared policy semantics.
    Outputs: per-path cost/period, and per-path [waste,lost,order]/period.
    Nonfinite actions are errors. Copies prevent policy state mutation.
    """
    npaths, periods, _ = demands.shape
    if not 0 <= burnin < periods:
        raise ValueError("Invalid burnin")
    costs = np.zeros(npaths)
    components = np.zeros((npaths, 3))
    for path in range(npaths):
        age = np.zeros(m, dtype=np.int64)
        pipeline = np.zeros(max(0, L - 1), dtype=np.int64)
        for t in range(periods):
            raw_order = policy(age.copy(), pipeline.copy(), theta, mu, cv, f, L)
            if not np.isfinite(raw_order):
                raise ValueError("Nonfinite policy action")
            raw_order = max(0.0, raw_order)
            if cap >= 0:
                raw_order = min(raw_order, max(0, cap - age.sum() - pipeline.sum()))
            if raw_order > 1e12:
                raise ValueError("Numerically unsafe policy action")
            order = int(np.rint(raw_order))
            waste, lost, held = transition_inplace(
                age, pipeline, order, demands[path, t, 0], demands[path, t, 1], L)
            if t >= burnin:
                costs[path] += w * waste + p * lost + h * held
                components[path, 0] += waste
                components[path, 1] += lost
                components[path, 2] += order
    return costs / (periods - burnin), components / (periods - burnin)


def evaluate(scenario: Scenario, demands: np.ndarray, policy: Callable,
             theta: np.ndarray, burnin: int = 200):
    return evaluate_kernel(policy, np.asarray(theta, dtype=float), demands,
                           scenario.m, scenario.L, inventory_cap(scenario),
                           scenario.mean, scenario.sd / scenario.mean, scenario.f,
                           scenario.h, scenario.p, scenario.w, burnin)


def evaluate_python(scenario: Scenario, demands: np.ndarray, policy: Callable,
                    burnin: int = 200):
    """Reference evaluator for arbitrary policy(age,pipeline)->scalar callbacks.

    Shares demand paths, transitions, integer projection, and objective with
    evaluate(). Runtime is deliberately not restricted by the model semantics.
    """
    demands = np.asarray(demands)
    if demands.ndim != 3 or demands.shape[-1] != 2:
        raise ValueError("Demands must have shape [paths,periods,2]")
    npaths, periods, _ = demands.shape
    if not 0 <= burnin < periods:
        raise ValueError("Invalid burnin")
    costs = np.zeros(npaths)
    components = np.zeros((npaths, 3))
    cap = inventory_cap(scenario)
    for path in range(npaths):
        age = np.zeros(scenario.m, dtype=np.int64)
        pipeline = np.zeros(max(0, scenario.L - 1), dtype=np.int64)
        for t in range(periods):
            raw_order = float(policy(age.copy(), pipeline.copy()))
            if not np.isfinite(raw_order):
                raise ValueError("Nonfinite policy action")
            raw_order = max(0.0, raw_order)
            if cap >= 0:
                raw_order = min(raw_order, max(0, cap - int(age.sum()) - int(pipeline.sum())))
            if raw_order > 1e12:
                raise ValueError("Numerically unsafe policy action")
            order = int(np.rint(raw_order))
            waste, lost, held = transition_inplace(age, pipeline, order,
                                                  int(demands[path, t, 0]),
                                                  int(demands[path, t, 1]), scenario.L)
            if t >= burnin:
                costs[path] += scenario.w * waste + scenario.p * lost + scenario.h * held
                components[path] += (waste, lost, order)
    return costs / (periods - burnin), components / (periods - burnin)


def handcheck() -> dict:
    """Meaningful event-order, moment, and upstream-transition verification."""
    # Old stock is preserved by LIFO and hence expires; FIFO prevents waste.
    age = np.array([3, 0, 4], dtype=np.int64)
    pipe = np.array([2], dtype=np.int64)
    assert transition_inplace(age, pipe, 5, 0, 4, 2) == (3, 0, 0)
    assert np.array_equal(age, [0, 0, 2]) and np.array_equal(pipe, [5])
    age = np.array([3, 0, 4], dtype=np.int64)
    pipe = np.array([2], dtype=np.int64)
    assert transition_inplace(age, pipe, 5, 4, 0, 2) == (0, 0, 3)
    assert np.array_equal(age, [0, 3, 2])
    # An order at t=0 is unavailable at t=0,1; it is fresh at t=2.
    age, pipe = np.zeros(3, dtype=np.int64), np.zeros(1, dtype=np.int64)
    wastes = []
    snapshots = []
    for t in range(5):
        snapshots.append(age.copy())
        wastes.append(transition_inplace(age, pipe, 5 if t == 0 else 0, 0, 0, 2)[0])
    assert np.array_equal(snapshots[1], [0, 0, 0])
    assert np.array_equal(snapshots[2], [0, 0, 5])
    assert wastes == [0, 0, 0, 0, 5]
    # Independent reference is a literal translation of upstream cumulative
    # inventory transition; random coverage includes shortage and mixed service.
    rng = np.random.default_rng(48191)
    for m in (3, 4, 5):
        for L in (1, 2, 3):
            for _ in range(500):
                age = rng.integers(0, 10, size=m, dtype=np.int64)
                pipe = rng.integers(0, 10, size=L - 1, dtype=np.int64)
                order, fifo, lifo = map(int, rng.integers(0, 30, size=3))
                state = np.cumsum(np.concatenate((age, pipe))).tolist()
                state.append(state[-1] + order)
                on_hand, total = state[m - 1], fifo + lifo
                lost, wasted = max(0, total - on_hand), 0
                if on_hand < total:
                    decrease = on_hand
                    state.pop(0)
                    state[:m - 1] = [0] * (m - 1)
                else:
                    for j in range(m):
                        state[j] = max(0, state[j] - fifo)
                    wasted = state.pop(0)
                    if lifo:
                        remaining = state[m - 2] - lifo
                        wasted = min(remaining, wasted)
                        for j in range(m - 1):
                            state[j] = min(remaining, state[j]) - wasted
                    else:
                        for j in range(m - 1):
                            state[j] -= wasted
                    decrease = total + wasted
                for j in range(m - 1, m + L - 1):
                    state[j] -= decrease
                got_waste, got_lost, _ = transition_inplace(age, pipe, order, fifo, lifo, L)
                assert (got_waste, got_lost) == (wasted, lost)
                assert np.array_equal(np.cumsum(np.concatenate((age, pipe))), state)
    max_mean_error = max_variance_error = 0.0
    for scenario in scenarios() + scenarios("legacy_code", "legacy_code"):
        for fraction in (scenario.f, 1 - scenario.f):
            mean, sd = fraction * scenario.mean, np.sqrt(fraction) * scenario.sd
            pmf = aer_pmf(mean, sd)
            support = np.arange(len(pmf))
            max_mean_error = max(max_mean_error, abs(float(support @ pmf) - mean))
            max_variance_error = max(max_variance_error, abs(float((support - mean) ** 2 @ pmf) - sd * sd))
            assert abs(support @ pmf - mean) < 1e-8
            assert abs((support - mean) ** 2 @ pmf - sd * sd) < 1e-6
    return {"upstream_transition_cases": 4500, "moment_scenarios": 24,
            "max_mean_error": max_mean_error, "max_variance_error": max_variance_error,
            "lead_time_and_expiry_handchecks": "passed"}


"""Identical derivative-free parameter optimizer used across all structure arms."""
import time
import numpy as np
from scipy.optimize import differential_evolution
from scipy.stats import qmc


def optimize(objective, bounds, initial, budget=256, seed=1):
    bounds = np.asarray(bounds, dtype=float)
    initial = np.asarray(initial, dtype=float)
    start = time.monotonic()
    nfev, best, best_x = 0, float('inf'), initial.copy()
    class Done(Exception):
        pass
    def fun(x):
        nonlocal nfev, best, best_x
        if nfev >= budget:
            raise Done()
        nfev += 1
        val = float(objective(x))
        if not np.isfinite(val):
            raise ValueError("Nonfinite simulation objective")
        if val < best:
            best, best_x = val, np.asarray(x).copy()
        return val
    fun(initial)
    if len(initial):
        pop = qmc.LatinHypercube(d=len(initial), seed=seed).random(16)
        pop = qmc.scale(pop, bounds[:, 0], bounds[:, 1])
        pop[0] = initial
        try:
            differential_evolution(fun, bounds, init=pop, maxiter=budget,
                                   mutation=(.4, 1.), recombination=.8,
                                   rng=seed, polish=False, tol=0., atol=0.)
        except Done:
            pass
    return {"theta": best_x.tolist(), "cost": best, "nfev": nfev,
            "seconds": time.monotonic()-start}

"""Trusted job body, run only inside a filesystem/network-isolated worker."""
import ast
import json
import math
import time
import numpy as np
from numba import njit


def run_numeric_job(job):
    # prepare_policy is injected from the audited numerical AST validator.
    prepared = prepare_policy(job['code'], None)
    ns = {}
    exec(compile(prepared['source'], 'candidate.py', 'exec'), ns)
    numeric = njit(ns['compute_order_amount'], boundscheck=True)
    @njit
    def policy(age, pipeline, theta, mu, cv, f, L):
        return numeric(age, pipeline, mu, cv, f, L, theta)
    bounds = [[c['min'], c['max']] for c in prepared['opt_params'].values()]
    initial = prepared['values']
    outputs = {}
    for spec in job['scenarios']:
        s = Scenario(**spec)
        cap = inventory_cap(s)
        tape = sample_demands(s, job['paths'], job['burnin']+job['horizon'], job['seed'])
        def evaluate(theta):
            return evaluate_kernel(policy, np.asarray(theta, dtype=float), tape,
                                   s.m, s.L, cap, s.mean, s.sd/s.mean, s.f,
                                   s.h, s.p, s.w, job['burnin'])
        if job['op'] == 'fit':
            record = optimize(lambda th: evaluate(th)[0].mean(), bounds, initial,
                              job['budget'], job['optimizer_seed'])
        else:
            record = {'theta': job['theta'][s.name], 'nfev': 0}
        costs, metrics = evaluate(record['theta'])
        record.update(cost=float(np.mean(costs)), path_costs=costs.tolist(),
                      metrics=np.mean(metrics, axis=0).tolist(), cap=cap)
        outputs[s.name] = record
    return {'results': outputs, 'parameters': prepared['opt_params'],
            'structure_sha256': prepared['structure_sha256'],
            'code_sha256': prepared['code_sha256'],
            'import_normalization': prepared.get('import_normalization', [])}
