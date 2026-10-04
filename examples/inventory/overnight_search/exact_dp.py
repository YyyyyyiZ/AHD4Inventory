"""Finite-state average-cost dynamic program for the primary perishable cases.

This is a classical OR oracle, not AIPS. Demand tails are collapsed exactly for
inventory transitions; expected shortage uses the exact untruncated demand mean.
The final-test command requires an explicit --test-authorized flag after freeze.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
from numba import njit
from scipy import stats

from .perishable import (Scenario, _aer_components, aer_pmf, evaluate,
                         evaluate_python, inventory_cap, sample_demands,
                         scenarios, transition_inplace)


OUT = Path("output/overnight_search/20260917/dp")


@dataclass
class Model:
    scenario: Scenario
    cap: int
    states: np.ndarray
    base: np.ndarray
    offsets: np.ndarray
    next_bases: np.ndarray
    probabilities: np.ndarray
    costs: np.ndarray
    max_actions: np.ndarray


def capped_pmf(mean, sd, cap):
    """Distribution of min(D,cap), with tail probability obtained from sf."""
    if cap == 0:
        return np.ones(1)
    components = _aer_components(mean, sd)
    if components[0][1] is None:
        result = np.zeros(cap + 1)
        result[0] = 1
        return result
    support = np.arange(cap)
    result = np.zeros(cap + 1)
    for weight, distribution in components:
        result[:cap] += weight * distribution.pmf(support)
        result[cap] += weight * distribution.sf(cap - 1)
    assert abs(result.sum() - 1) < 1e-12
    return result


def age_outcomes(age, fifo_pmf, lifo_pmf):
    """Independent scalar transition implementation for DP construction."""
    distribution = {}
    sold_expected, waste_expected, held_expected = 0.0, 0.0, 0.0
    for fifo, fp in enumerate(fifo_pmf):
        if fp == 0:
            continue
        for lifo, lp in enumerate(lifo_pmf):
            probability = float(fp * lp)
            if probability == 0:
                continue
            remaining = list(age)
            demand = fifo
            for j in range(3):
                sold = min(remaining[j], demand)
                remaining[j] -= sold
                demand -= sold
            demand = lifo
            for j in (2, 1, 0):
                sold = min(remaining[j], demand)
                remaining[j] -= sold
                demand -= sold
            sold_expected += probability * (sum(age) - sum(remaining))
            waste_expected += probability * remaining[0]
            held_expected += probability * (remaining[1] + remaining[2])
            key = (remaining[1], remaining[2])
            distribution[key] = distribution.get(key, 0.0) + probability
    assert abs(sum(distribution.values()) - 1) < 1e-12
    return distribution, sold_expected, waste_expected, held_expected


def build_model(scenario):
    if scenario.m != 3 or scenario.L != 2:
        raise ValueError("This exact implementation supports m=3,L=2 only.")
    cap = inventory_cap(scenario)
    if cap < 0:
        raise ValueError("A finite inventory-position cap is required.")
    base = np.full((cap + 1,) * 3, -1, dtype=np.int64)
    states = []
    for a in range(cap + 1):
        for b in range(cap + 1 - a):
            for c in range(cap + 1 - a - b):
                base[a, b, c] = len(states)
                for pipeline in range(cap + 1 - a - b - c):
                    states.append((a, b, c, pipeline))
    states = np.asarray(states, dtype=np.int64)
    capped = {}
    for total in range(cap + 1):
        capped[total] = [capped_pmf(fraction * scenario.mean, np.sqrt(fraction) * scenario.sd, total)
                         for fraction in (scenario.f, 1 - scenario.f)]
    cache = {}
    offsets, successor_bases, probabilities, costs = [0], [], [], []
    max_actions = cap - states.sum(axis=1)
    for a, b, c, pipeline in states:
        key = (int(a), int(b), int(c))
        if key not in cache:
            cache[key] = age_outcomes(key, *capped[a + b + c])
        distribution, expected_sales, expected_waste, expected_held = cache[key]
        expected_lost = scenario.mean - expected_sales
        assert expected_lost >= -1e-10
        costs.append(scenario.p * expected_lost + scenario.w * expected_waste + scenario.h * expected_held)
        for (remaining_b, remaining_c), probability in distribution.items():
            successor = int(base[remaining_b, remaining_c, pipeline])
            assert successor >= 0
            successor_bases.append(successor)
            probabilities.append(probability)
        offsets.append(len(successor_bases))
    return Model(scenario, cap, states, base, np.asarray(offsets, dtype=np.int64),
                 np.asarray(successor_bases, dtype=np.int64), np.asarray(probabilities),
                 np.asarray(costs), max_actions)


@njit(cache=True)
def bellman(bias, offsets, next_bases, probabilities, costs, max_actions):
    values = np.empty_like(bias)
    actions = np.zeros(len(bias), dtype=np.int64)
    for state in range(len(bias)):
        best = np.inf
        for action in range(max_actions[state] + 1):
            expected = 0.0
            for j in range(offsets[state], offsets[state + 1]):
                expected += probabilities[j] * bias[next_bases[j] + action]
            if expected < best:
                best = expected
                actions[state] = action
        values[state] = costs[state] + best
    return values, actions


def solve(model, tolerance=1e-8, max_iterations=20000):
    start = time.perf_counter()
    bias = np.zeros(len(model.states))
    for iteration in range(1, max_iterations + 1):
        values, actions = bellman(bias, model.offsets, model.next_bases, model.probabilities,
                                  model.costs, model.max_actions)
        increment = values - bias
        lower, upper = float(increment.min()), float(increment.max())
        span = upper - lower
        if iteration % 500 == 0:
            print(json.dumps(dict(scenario=model.scenario.name, iteration=iteration,
                                  lower=lower, upper=upper, span=span)), flush=True)
        if span <= tolerance:
            return actions, bias, dict(iterations=iteration, gain_lower=lower, gain_upper=upper,
                                      bellman_span=span, tolerance=tolerance,
                                      seconds=time.perf_counter() - start)
        # Lazy relative value iteration avoids possible periodicity. The residual
        # and its bounds above always use the original, undamped Bellman operator.
        bias = 0.5 * bias + 0.5 * (values - values[0])
    raise RuntimeError(f"RVI did not certify convergence: final span={span}")


@njit(cache=True)
def table_policy(age, pipeline, theta, mu, cv, f, L):
    width = int(theta[0]) + 1
    address = 1 + (age[0] * width + age[1]) * width + age[2]
    state = int(theta[address]) + pipeline[0]
    return theta[1 + width ** 3 + state]


def pack_policy(model, actions):
    return np.concatenate((np.array([model.cap]), model.base.ravel(), actions)).astype(float)


@njit(cache=True)
def brute_pmf_row(state, action, fifo, lifo, base, nstates, h, p, w):
    """Cross-check using the public simulator and its long, truncated PMF."""
    row = np.zeros(nstates)
    cost = 0.0
    for df in range(len(fifo)):
        for dl in range(len(lifo)):
            probability = fifo[df] * lifo[dl]
            if probability == 0:
                continue
            age = state[:3].copy()
            pipeline = state[3:].copy()
            waste, lost, held = transition_inplace(age, pipeline, action, df, dl, 2)
            successor = base[age[0], age[1], age[2]] + pipeline[0]
            row[successor] += probability
            cost += probability * (h * held + p * lost + w * waste)
    return row, cost


def crosscheck_model(model, actions):
    scenario = model.scenario
    rng = np.random.default_rng(17095001)
    checks = []
    selected = np.unique(np.r_[0, len(model.states) - 1, rng.integers(0, len(model.states), 6)])
    pmfs = [aer_pmf(fraction * scenario.mean, np.sqrt(fraction) * scenario.sd, 1e-14)
            for fraction in (scenario.f, 1 - scenario.f)]
    for index in selected:
        action = int(actions[index])
        actual, brute_cost = brute_pmf_row(model.states[index], action, pmfs[0], pmfs[1],
                                           model.base, len(model.states), scenario.h, scenario.p, scenario.w)
        expected = np.zeros(len(model.states))
        lo, hi = model.offsets[index:index + 2]
        np.add.at(expected, model.next_bases[lo:hi] + action, model.probabilities[lo:hi])
        probability_error = float(np.abs(actual - expected).sum())
        cost_error = abs(float(brute_cost - model.costs[index]))
        assert probability_error < 1e-10 and cost_error < 1e-7
        checks.append(dict(state=model.states[index].tolist(), action=action,
                           transition_l1_error=probability_error, expected_cost_error=cost_error))
    theta = pack_policy(model, actions)
    demands = sample_demands(scenario, 3, 100, 17095002)
    fast_cost, fast_components = evaluate(scenario, demands, table_policy, theta, burnin=20)
    def callback(age, pipeline):
        return int(actions[model.base[tuple(age)] + pipeline[0]])
    reference_cost, reference_components = evaluate_python(scenario, demands, callback, burnin=20)
    assert np.array_equal(fast_cost, reference_cost)
    assert np.array_equal(fast_components, reference_components)
    return dict(brute_pmf_checks=checks, evaluator_paths=3, evaluator_periods=100,
                evaluator_costs=fast_cost.tolist(), evaluators_agree_exactly=True)


def simulation_summary(scenario, theta, *, seed, paths, burnin, horizon):
    demands = sample_demands(scenario, paths, burnin + horizon, seed)
    costs, components = evaluate(scenario, demands, table_policy, theta, burnin=burnin)
    sem = float(stats.sem(costs))
    radius = float(stats.t.ppf(.975, paths - 1) * sem)
    mean = float(costs.mean())
    return dict(seed=seed, paths=paths, burnin=burnin, horizon=horizon, mean=mean,
                standard_error=sem, ci95=[mean - radius, mean + radius],
                path_costs=costs.tolist(), mean_components=components.mean(axis=0).tolist(),
                path_components=components.tolist())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["solve", "test"])
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--test-authorized", action="store_true")
    parser.add_argument("--tolerance", type=float, default=1e-8)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.command == "test" and not args.test_authorized:
        parser.error("The final test is sealed until root authorizes after freezing all methods.")
    reports = []
    for index, scenario in enumerate(s for s in scenarios() if s.m == 3):
        destination = args.out / scenario.name
        destination.mkdir(exist_ok=True)
        if args.command == "solve":
            started = time.perf_counter()
            model = build_model(scenario)
            build_seconds = time.perf_counter() - started
            print(json.dumps(dict(scenario=scenario.name, states=len(model.states), cap=model.cap,
                                  transitions=len(model.probabilities), build_seconds=build_seconds)), flush=True)
            actions, bias, certificate = solve(model, args.tolerance)
            checks = crosscheck_model(model, actions)
            theta = pack_policy(model, actions)
            np.savez_compressed(destination / "policy.npz", theta=theta, actions=actions,
                                states=model.states, base=model.base, bias=bias)
            validation = simulation_summary(scenario, theta, seed=17096001 + index,
                                             paths=64, burnin=500, horizon=6000)
            report = dict(label="Classical exact finite-state OR benchmark; not AIPS", scenario=scenario.to_dict(),
                          nstates=len(model.states), transitions=len(model.probabilities), build_seconds=build_seconds,
                          certificate=certificate, checks=checks, validation=validation,
                          python=platform.python_version(), numpy=np.__version__,
                          model_source_sha256=hashlib.sha256(Path(__file__).with_name("perishable.py").read_bytes()).hexdigest(),
                          solver_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            (destination / "result.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(dict(scenario=scenario.name, certificate=certificate,
                                  validation_mean=validation["mean"], validation_ci95=validation["ci95"])), flush=True)
        else:
            saved = np.load(destination / "policy.npz")
            report = dict(scenario=scenario.name, test=simulation_summary(scenario, saved["theta"],
                          seed=17094001, paths=128, burnin=500, horizon=3000))
            (destination / "test.json").write_text(json.dumps(report, indent=2) + "\n")
        reports.append(report)
    (args.out / ("summary.json" if args.command == "solve" else "test_summary.json")).write_text(
        json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()
