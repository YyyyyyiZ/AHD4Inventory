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


if __name__ == "__main__":
    import json
    print(json.dumps({"checks": handcheck(), "scenarios": [s.to_dict() for s in scenarios()]}, indent=2))
