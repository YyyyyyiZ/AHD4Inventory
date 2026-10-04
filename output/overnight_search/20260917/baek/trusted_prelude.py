"""Perishable-inventory screening model, with explicit source discrepancies.

Policy state is quantities by remaining life (oldest first) after receipt and
orders due in 1,...,L-1 periods. See docs/overnight_perishable_spec.md.
No API calls occur in this module.
"""
from __future__ import annotations
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
    demand_mode: str = 'paper_cv'
    cap_mode: str = 'paper'

    @property
    def sd(self) -> float:
        if self.demand_mode == 'paper_cv':
            return self.cv * self.mean
        if self.demand_mode == 'legacy_code':
            return self.cv * np.sqrt(self.mean)
        raise ValueError(f'Unknown demand mode: {self.demand_mode}')

    def to_dict(self) -> dict:
        return {**asdict(self), 'actual_cv': self.sd / self.mean, 'inventory_cap': inventory_cap(self)}

def _aer_components(mean: float, sd: float):
    """Adan--van Eenige--Resing two-moment fit, matching DynaPlex formulas.

    Returns (mixture weight, scipy discrete distribution) pairs. These are
    untruncated laws; only the numerical PMF used to calculate caps is cut off.
    """
    if mean == 0:
        return [(1.0, None)]
    if mean < 0 or sd < 0:
        raise ValueError('Mean and SD must be nonnegative')
    fractional = mean - np.floor(mean)
    if sd * sd < fractional * (1 - fractional) - 1e-10:
        raise ValueError('These moments cannot define an integer-valued law')
    a = (sd / mean) ** 2 - 1 / mean
    if abs(a) < 1e-06:
        return [(1.0, stats.poisson(mean))]
    if a < 0:
        if abs(a + 1) < 1e-10:
            return [(1.0, stats.binom(1, mean))]
        k = int(np.floor(1 / -a))
        q = (1 + a * (1 + k) + np.sqrt(max(0, -a * k * (1 + k) - k))) / (1 + a)
        probability = mean / (k + 1 - q)
        return [(float(np.clip(q, 0, 1)), stats.binom(k, probability)), (float(np.clip(1 - q, 0, 1)), stats.binom(k + 1, probability))]
    if a < 1:
        k = int(np.floor(1 / a))
        q = ((1 + k) * a - np.sqrt(max(0, (1 + k) * (1 - a * k)))) / (1 + a)
        failure = mean / (k + 1 - q + mean)
        return [(float(np.clip(q, 0, 1)), stats.nbinom(k, 1 - failure)), (float(np.clip(1 - q, 0, 1)), stats.nbinom(k + 1, 1 - failure))]
    positive = 1 + a + np.sqrt(a * a - 1)
    negative = 1 + a - np.sqrt(a * a - 1)
    weight = 1 / positive
    return [(weight, stats.nbinom(1, 2 / (2 + mean * positive))), (1 - weight, stats.nbinom(1, 2 / (2 + mean * negative)))]

@lru_cache(maxsize=128)
def aer_pmf(mean: float, sd: float, tail: float=1e-13) -> np.ndarray:
    """PMF with a numerically negligible tail removed and then normalized."""
    components = _aer_components(mean, sd)
    if components[0][1] is None:
        return np.array([1.0])
    maximum = max((int(dist.isf(tail)) for weight, dist in components if weight > 0))
    support = np.arange(maximum + 1)
    pmf = sum((weight * dist.pmf(support) for weight, dist in components))
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
        components = _aer_components(fraction * scenario.mean, np.sqrt(fraction) * scenario.sd)
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
    if scenario.cap_mode == 'none':
        return -1
    if scenario.cap_mode not in ('paper', 'legacy_code'):
        raise ValueError(f'Unknown cap mode: {scenario.cap_mode}')
    fifo = aer_pmf(scenario.f * scenario.mean, np.sqrt(scenario.f) * scenario.sd)
    lifo = aer_pmf((1 - scenario.f) * scenario.mean, np.sqrt(1 - scenario.f) * scenario.sd)
    daily = np.convolve(fifo, lifo)
    periods = scenario.m + scenario.L + int(scenario.cap_mode == 'legacy_code')
    total = np.array([1.0])
    for _ in range(periods):
        total = np.convolve(total, daily)
    return int(np.searchsorted(np.cumsum(total), scenario.p / (scenario.p + scenario.w)))

@njit(cache=False)
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
    return (wasted, remaining_fifo + remaining_lifo, held)

@njit(cache=False)
def evaluate_kernel(policy, theta, demands, m, L, cap, mu, cv, f, h, p, w, burnin):
    """Fast shared evaluator. `policy` must be a Numba dispatcher.

    policy(age,pipeline,theta,mu,cv,f,L)->scalar. Half-even integer rounding
    and clipping to the inventory-position cap are shared policy semantics.
    Outputs: per-path cost/period, and per-path [waste,lost,order]/period.
    Nonfinite actions are errors. Copies prevent policy state mutation.
    """
    npaths, periods, _ = demands.shape
    if not 0 <= burnin < periods:
        raise ValueError('Invalid burnin')
    costs = np.zeros(npaths)
    components = np.zeros((npaths, 3))
    for path in range(npaths):
        age = np.zeros(m, dtype=np.int64)
        pipeline = np.zeros(max(0, L - 1), dtype=np.int64)
        for t in range(periods):
            raw_order = policy(age.copy(), pipeline.copy(), theta, mu, cv, f, L)
            if not np.isfinite(raw_order):
                raise ValueError('Nonfinite policy action')
            raw_order = max(0.0, raw_order)
            if cap >= 0:
                raw_order = min(raw_order, max(0, cap - age.sum() - pipeline.sum()))
            if raw_order > 1000000000000.0:
                raise ValueError('Numerically unsafe policy action')
            order = int(np.rint(raw_order))
            waste, lost, held = transition_inplace(age, pipeline, order, demands[path, t, 0], demands[path, t, 1], L)
            if t >= burnin:
                costs[path] += w * waste + p * lost + h * held
                components[path, 0] += waste
                components[path, 1] += lost
                components[path, 2] += order
    return (costs / (periods - burnin), components / (periods - burnin))

def evaluate(scenario: Scenario, demands: np.ndarray, policy: Callable, theta: np.ndarray, burnin: int=200):
    return evaluate_kernel(policy, np.asarray(theta, dtype=float), demands, scenario.m, scenario.L, inventory_cap(scenario), scenario.mean, scenario.sd / scenario.mean, scenario.f, scenario.h, scenario.p, scenario.w, burnin)

def evaluate_python(scenario: Scenario, demands: np.ndarray, policy: Callable, burnin: int=200):
    """Reference evaluator for arbitrary policy(age,pipeline)->scalar callbacks.

    Shares demand paths, transitions, integer projection, and objective with
    evaluate(). Runtime is deliberately not restricted by the model semantics.
    """
    demands = np.asarray(demands)
    if demands.ndim != 3 or demands.shape[-1] != 2:
        raise ValueError('Demands must have shape [paths,periods,2]')
    npaths, periods, _ = demands.shape
    if not 0 <= burnin < periods:
        raise ValueError('Invalid burnin')
    costs = np.zeros(npaths)
    components = np.zeros((npaths, 3))
    cap = inventory_cap(scenario)
    for path in range(npaths):
        age = np.zeros(scenario.m, dtype=np.int64)
        pipeline = np.zeros(max(0, scenario.L - 1), dtype=np.int64)
        for t in range(periods):
            raw_order = float(policy(age.copy(), pipeline.copy()))
            if not np.isfinite(raw_order):
                raise ValueError('Nonfinite policy action')
            raw_order = max(0.0, raw_order)
            if cap >= 0:
                raw_order = min(raw_order, max(0, cap - int(age.sum()) - int(pipeline.sum())))
            if raw_order > 1000000000000.0:
                raise ValueError('Numerically unsafe policy action')
            order = int(np.rint(raw_order))
            waste, lost, held = transition_inplace(age, pipeline, order, int(demands[path, t, 0]), int(demands[path, t, 1]), scenario.L)
            if t >= burnin:
                costs[path] += scenario.w * waste + scenario.p * lost + scenario.h * held
                components[path] += (waste, lost, order)
    return (costs / (periods - burnin), components / (periods - burnin))
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


def scenario_from_params(params):
    fields = {name: params[name] for name in Scenario.__dataclass_fields__ if name in params}
    fields.setdefault("name", "anonymous_instance")
    return Scenario(**fields)

def training_demands(params):
    return sample_demands(scenario_from_params(params), 8, 200+512, 17091001)

def simulate(policy, params, demands=None, *, npaths=8, burnin=200, horizon=512, seed=17091001):
    """Score arbitrary scalar policy(age,pipeline); return mean and path costs.

    Exact trusted transitions are used; attempts optional Numba acceleration,
    falling back to unrestricted Python callback evaluation if compilation fails.
    """
    s = scenario_from_params(params)
    if demands is None:
        demands = sample_demands(s, npaths, burnin+horizon, seed)
    backend = "python"
    try:
        compiled = policy if hasattr(policy, "py_func") else njit(policy)
        def adapter(age, pipeline, theta, mu, cv, f, L):
            return compiled(age, pipeline)
        fast = njit(adapter)
        costs, components = evaluate(s, demands, fast, np.empty(0), burnin)
        backend = "numba"
    except Exception:
        costs, components = evaluate_python(s, demands, policy, burnin)
    return {"mean_cost": float(costs.mean()), "path_costs": costs,
            "components": components, "backend": backend}

TRUSTED_BENCHMARK_SOURCE = '"""Perishable-inventory screening model, with explicit source discrepancies.\n\nPolicy state is quantities by remaining life (oldest first) after receipt and\norders due in 1,...,L-1 periods. See docs/overnight_perishable_spec.md.\nNo API calls occur in this module.\n"""\nfrom __future__ import annotations\nfrom dataclasses import asdict, dataclass\nfrom functools import lru_cache\nfrom typing import Callable\nimport numpy as np\nfrom numba import njit\nfrom scipy import stats\n\n@dataclass(frozen=True)\nclass Scenario:\n    name: str\n    m: int\n    L: int\n    cv: float\n    f: float\n    mean: float = 4.0\n    h: float = 0.0\n    p: float = 100.0\n    w: float = 100.0\n    demand_mode: str = \'paper_cv\'\n    cap_mode: str = \'paper\'\n\n    @property\n    def sd(self) -> float:\n        if self.demand_mode == \'paper_cv\':\n            return self.cv * self.mean\n        if self.demand_mode == \'legacy_code\':\n            return self.cv * np.sqrt(self.mean)\n        raise ValueError(f\'Unknown demand mode: {self.demand_mode}\')\n\n    def to_dict(self) -> dict:\n        return {**asdict(self), \'actual_cv\': self.sd / self.mean, \'inventory_cap\': inventory_cap(self)}\n\ndef _aer_components(mean: float, sd: float):\n    """Adan--van Eenige--Resing two-moment fit, matching DynaPlex formulas.\n\n    Returns (mixture weight, scipy discrete distribution) pairs. These are\n    untruncated laws; only the numerical PMF used to calculate caps is cut off.\n    """\n    if mean == 0:\n        return [(1.0, None)]\n    if mean < 0 or sd < 0:\n        raise ValueError(\'Mean and SD must be nonnegative\')\n    fractional = mean - np.floor(mean)\n    if sd * sd < fractional * (1 - fractional) - 1e-10:\n        raise ValueError(\'These moments cannot define an integer-valued law\')\n    a = (sd / mean) ** 2 - 1 / mean\n    if abs(a) < 1e-06:\n        return [(1.0, stats.poisson(mean))]\n    if a < 0:\n        if abs(a + 1) < 1e-10:\n            return [(1.0, stats.binom(1, mean))]\n        k = int(np.floor(1 / -a))\n        q = (1 + a * (1 + k) + np.sqrt(max(0, -a * k * (1 + k) - k))) / (1 + a)\n        probability = mean / (k + 1 - q)\n        return [(float(np.clip(q, 0, 1)), stats.binom(k, probability)), (float(np.clip(1 - q, 0, 1)), stats.binom(k + 1, probability))]\n    if a < 1:\n        k = int(np.floor(1 / a))\n        q = ((1 + k) * a - np.sqrt(max(0, (1 + k) * (1 - a * k)))) / (1 + a)\n        failure = mean / (k + 1 - q + mean)\n        return [(float(np.clip(q, 0, 1)), stats.nbinom(k, 1 - failure)), (float(np.clip(1 - q, 0, 1)), stats.nbinom(k + 1, 1 - failure))]\n    positive = 1 + a + np.sqrt(a * a - 1)\n    negative = 1 + a - np.sqrt(a * a - 1)\n    weight = 1 / positive\n    return [(weight, stats.nbinom(1, 2 / (2 + mean * positive))), (1 - weight, stats.nbinom(1, 2 / (2 + mean * negative)))]\n\n@lru_cache(maxsize=128)\ndef aer_pmf(mean: float, sd: float, tail: float=1e-13) -> np.ndarray:\n    """PMF with a numerically negligible tail removed and then normalized."""\n    components = _aer_components(mean, sd)\n    if components[0][1] is None:\n        return np.array([1.0])\n    maximum = max((int(dist.isf(tail)) for weight, dist in components if weight > 0))\n    support = np.arange(maximum + 1)\n    pmf = sum((weight * dist.pmf(support) for weight, dist in components))\n    pmf /= pmf.sum()\n    return pmf\n\ndef sample_demands(scenario: Scenario, npaths: int, periods: int, seed: int) -> np.ndarray:\n    """Independent FIFO and LIFO streams; last axis is [FIFO, LIFO].\n\n    Group means are f*mu and (1-f)*mu, with variances f*SD^2 and\n    (1-f)*SD^2. A binomial splitting of one total draw is a different model.\n    """\n    rng = np.random.default_rng(seed)\n    shape = (npaths, periods)\n    demands = np.zeros((*shape, 2), dtype=np.int64)\n    for channel, fraction in enumerate((scenario.f, 1 - scenario.f)):\n        components = _aer_components(fraction * scenario.mean, np.sqrt(fraction) * scenario.sd)\n        if components[0][1] is None:\n            continue\n        if len(components) == 1:\n            demands[:, :, channel] = components[0][1].rvs(size=shape, random_state=rng)\n        else:\n            choose_first = rng.random(shape) < components[0][0]\n            first = components[0][1].rvs(size=shape, random_state=rng)\n            second = components[1][1].rvs(size=shape, random_state=rng)\n            demands[:, :, channel] = np.where(choose_first, first, second)\n    return demands\n\n@lru_cache(maxsize=128)\ndef inventory_cap(scenario: Scenario) -> int:\n    """Newsvendor fractile of demand over m+L (paper) or m+L+1 (code)."""\n    if scenario.cap_mode == \'none\':\n        return -1\n    if scenario.cap_mode not in (\'paper\', \'legacy_code\'):\n        raise ValueError(f\'Unknown cap mode: {scenario.cap_mode}\')\n    fifo = aer_pmf(scenario.f * scenario.mean, np.sqrt(scenario.f) * scenario.sd)\n    lifo = aer_pmf((1 - scenario.f) * scenario.mean, np.sqrt(1 - scenario.f) * scenario.sd)\n    daily = np.convolve(fifo, lifo)\n    periods = scenario.m + scenario.L + int(scenario.cap_mode == \'legacy_code\')\n    total = np.array([1.0])\n    for _ in range(periods):\n        total = np.convolve(total, daily)\n    return int(np.searchsorted(np.cumsum(total), scenario.p / (scenario.p + scenario.w)))\n\n@njit(cache=False)\ndef transition_inplace(age, pipeline, order, fifo, lifo, L):\n    """Serve FIFO then LIFO; expire oldest; age; receive next-period stock.\n\n    Returns (wasted units, lost units, held surviving units). Assumes feasible\n    integer order. Both state arrays are updated to the next decision epoch.\n    """\n    m = len(age)\n    if L == 0:\n        age[m - 1] += order\n    remaining_fifo = fifo\n    for j in range(m):\n        sold = min(age[j], remaining_fifo)\n        age[j] -= sold\n        remaining_fifo -= sold\n    remaining_lifo = lifo\n    for j in range(m - 1, -1, -1):\n        sold = min(age[j], remaining_lifo)\n        age[j] -= sold\n        remaining_lifo -= sold\n    wasted = age[0]\n    held = age.sum() - wasted\n    for j in range(m - 1):\n        age[j] = age[j + 1]\n    age[m - 1] = 0\n    if L == 1:\n        age[m - 1] = order\n    elif L > 1:\n        age[m - 1] = pipeline[0]\n        for j in range(len(pipeline) - 1):\n            pipeline[j] = pipeline[j + 1]\n        pipeline[len(pipeline) - 1] = order\n    return (wasted, remaining_fifo + remaining_lifo, held)\n\n@njit(cache=False)\ndef evaluate_kernel(policy, theta, demands, m, L, cap, mu, cv, f, h, p, w, burnin):\n    """Fast shared evaluator. `policy` must be a Numba dispatcher.\n\n    policy(age,pipeline,theta,mu,cv,f,L)->scalar. Half-even integer rounding\n    and clipping to the inventory-position cap are shared policy semantics.\n    Outputs: per-path cost/period, and per-path [waste,lost,order]/period.\n    Nonfinite actions are errors. Copies prevent policy state mutation.\n    """\n    npaths, periods, _ = demands.shape\n    if not 0 <= burnin < periods:\n        raise ValueError(\'Invalid burnin\')\n    costs = np.zeros(npaths)\n    components = np.zeros((npaths, 3))\n    for path in range(npaths):\n        age = np.zeros(m, dtype=np.int64)\n        pipeline = np.zeros(max(0, L - 1), dtype=np.int64)\n        for t in range(periods):\n            raw_order = policy(age.copy(), pipeline.copy(), theta, mu, cv, f, L)\n            if not np.isfinite(raw_order):\n                raise ValueError(\'Nonfinite policy action\')\n            raw_order = max(0.0, raw_order)\n            if cap >= 0:\n                raw_order = min(raw_order, max(0, cap - age.sum() - pipeline.sum()))\n            if raw_order > 1000000000000.0:\n                raise ValueError(\'Numerically unsafe policy action\')\n            order = int(np.rint(raw_order))\n            waste, lost, held = transition_inplace(age, pipeline, order, demands[path, t, 0], demands[path, t, 1], L)\n            if t >= burnin:\n                costs[path] += w * waste + p * lost + h * held\n                components[path, 0] += waste\n                components[path, 1] += lost\n                components[path, 2] += order\n    return (costs / (periods - burnin), components / (periods - burnin))\n\ndef evaluate(scenario: Scenario, demands: np.ndarray, policy: Callable, theta: np.ndarray, burnin: int=200):\n    return evaluate_kernel(policy, np.asarray(theta, dtype=float), demands, scenario.m, scenario.L, inventory_cap(scenario), scenario.mean, scenario.sd / scenario.mean, scenario.f, scenario.h, scenario.p, scenario.w, burnin)\n\ndef evaluate_python(scenario: Scenario, demands: np.ndarray, policy: Callable, burnin: int=200):\n    """Reference evaluator for arbitrary policy(age,pipeline)->scalar callbacks.\n\n    Shares demand paths, transitions, integer projection, and objective with\n    evaluate(). Runtime is deliberately not restricted by the model semantics.\n    """\n    demands = np.asarray(demands)\n    if demands.ndim != 3 or demands.shape[-1] != 2:\n        raise ValueError(\'Demands must have shape [paths,periods,2]\')\n    npaths, periods, _ = demands.shape\n    if not 0 <= burnin < periods:\n        raise ValueError(\'Invalid burnin\')\n    costs = np.zeros(npaths)\n    components = np.zeros((npaths, 3))\n    cap = inventory_cap(scenario)\n    for path in range(npaths):\n        age = np.zeros(scenario.m, dtype=np.int64)\n        pipeline = np.zeros(max(0, scenario.L - 1), dtype=np.int64)\n        for t in range(periods):\n            raw_order = float(policy(age.copy(), pipeline.copy()))\n            if not np.isfinite(raw_order):\n                raise ValueError(\'Nonfinite policy action\')\n            raw_order = max(0.0, raw_order)\n            if cap >= 0:\n                raw_order = min(raw_order, max(0, cap - int(age.sum()) - int(pipeline.sum())))\n            if raw_order > 1000000000000.0:\n                raise ValueError(\'Numerically unsafe policy action\')\n            order = int(np.rint(raw_order))\n            waste, lost, held = transition_inplace(age, pipeline, order, int(demands[path, t, 0]), int(demands[path, t, 1]), scenario.L)\n            if t >= burnin:\n                costs[path] += scenario.w * waste + scenario.p * lost + scenario.h * held\n                components[path] += (waste, lost, order)\n    return (costs / (periods - burnin), components / (periods - burnin))\n"""Identical derivative-free parameter optimizer used across all structure arms."""\nimport time\nimport numpy as np\nfrom scipy.optimize import differential_evolution\nfrom scipy.stats import qmc\n\n\ndef optimize(objective, bounds, initial, budget=256, seed=1):\n    bounds = np.asarray(bounds, dtype=float)\n    initial = np.asarray(initial, dtype=float)\n    start = time.monotonic()\n    nfev, best, best_x = 0, float(\'inf\'), initial.copy()\n    class Done(Exception):\n        pass\n    def fun(x):\n        nonlocal nfev, best, best_x\n        if nfev >= budget:\n            raise Done()\n        nfev += 1\n        val = float(objective(x))\n        if not np.isfinite(val):\n            raise ValueError("Nonfinite simulation objective")\n        if val < best:\n            best, best_x = val, np.asarray(x).copy()\n        return val\n    fun(initial)\n    if len(initial):\n        pop = qmc.LatinHypercube(d=len(initial), seed=seed).random(16)\n        pop = qmc.scale(pop, bounds[:, 0], bounds[:, 1])\n        pop[0] = initial\n        try:\n            differential_evolution(fun, bounds, init=pop, maxiter=budget,\n                                   mutation=(.4, 1.), recombination=.8,\n                                   rng=seed, polish=False, tol=0., atol=0.)\n        except Done:\n            pass\n    return {"theta": best_x.tolist(), "cost": best, "nfev": nfev,\n            "seconds": time.monotonic()-start}\n\n\ndef scenario_from_params(params):\n    fields = {name: params[name] for name in Scenario.__dataclass_fields__ if name in params}\n    fields.setdefault("name", "anonymous_instance")\n    return Scenario(**fields)\n\ndef training_demands(params):\n    return sample_demands(scenario_from_params(params), 8, 200+512, 17091001)\n\ndef simulate(policy, params, demands=None, *, npaths=8, burnin=200, horizon=512, seed=17091001):\n    """Score arbitrary scalar policy(age,pipeline); return mean and path costs.\n\n    Exact trusted transitions are used; attempts optional Numba acceleration,\n    falling back to unrestricted Python callback evaluation if compilation fails.\n    """\n    s = scenario_from_params(params)\n    if demands is None:\n        demands = sample_demands(s, npaths, burnin+horizon, seed)\n    backend = "python"\n    try:\n        compiled = policy if hasattr(policy, "py_func") else njit(policy)\n        def adapter(age, pipeline, theta, mu, cv, f, L):\n            return compiled(age, pipeline)\n        fast = njit(adapter)\n        costs, components = evaluate(s, demands, fast, np.empty(0), burnin)\n        backend = "numba"\n    except Exception:\n        costs, components = evaluate_python(s, demands, policy, burnin)\n    return {"mean_cost": float(costs.mean()), "path_costs": costs,\n            "components": components, "backend": backend}\n'
