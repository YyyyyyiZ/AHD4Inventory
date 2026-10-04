"""Free, independent scaling diagnostic; no main-experiment test data or LLMs.

The full fixed 16-scenario grid is reported. This probes classical policy
headroom and exact-state complexity, not AIPS or Baek performance.
"""
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from numba import njit
from scipy import signal, stats

from .optimization import optimize
from .perishable import Scenario, aer_pmf, evaluate_kernel, inventory_cap, sample_demands

OUT = Path("output/overnight_search/20260917/scaling_diagnostic")
PROTOCOL = dict(
    label="Classical policy and scaling diagnostic; no AIPS or Baek outcome claims",
    revision="Full feasible order-cap parameter range; initial range screen retained separately",
    grid=[dict(m=5, mean=20.), dict(m=5, mean=40.), dict(m=7, mean=4.), dict(m=8, mean=4.)],
    cv=[1.5, 2.], f=[0., .5], L=2,
    train=dict(paths=8, burnin=200, horizon=512, seed=1801001),
    validation=dict(paths=32, burnin=500, horizon=1000, seed=1802001),
    diagnostic_holdout=dict(paths=64, burnin=500, horizon=3000, seed=1804001),
    policies=["BSP", "CBS", "age_discount", "BSP_low_EW"],
    optimizer_evaluations_per_start=512, optimizer_seeds=[71, 171],
    strong_selection="Select age_discount or BSP_low_EW by validation mean, before diagnostic holdout",
    main_test_seed_opened=False,
)


def fast_cap(s):
    pmfs = [aer_pmf(fr * s.mean, np.sqrt(fr) * s.sd) for fr in (s.f, 1 - s.f)]
    daily = signal.fftconvolve(*pmfs)
    total = np.array([1.0])
    for _ in range(s.m + s.L):
        total = signal.fftconvolve(total, daily)
    total = np.maximum(total, 0)
    total /= total.sum()
    cumulative = np.cumsum(total)
    fractile = s.p / (s.p + s.w)
    cap = int(np.searchsorted(cumulative, fractile))
    return cap, dict(cdf_below=float(cumulative[cap - 1]) if cap else 0.,
                     cdf_at=float(cumulative[cap]), fractile=fractile)


def grid():
    result = []
    for g in PROTOCOL["grid"]:
        for cv in PROTOCOL["cv"]:
            for f in PROTOCOL["f"]:
                s = Scenario(f"scaling_m{g['m']}_mu{g['mean']:g}_cv{cv:g}_f{f:g}",
                             m=g["m"], mean=g["mean"], L=2, cv=cv, f=f)
                cap, quantile = fast_cap(s)
                dimension = s.m + s.L - 1
                states = math.comb(cap + dimension, dimension)
                state_actions = math.comb(cap + dimension + 1, dimension + 1)
                result.append(dict(scenario=asdict(s), cap=cap, quantile=quantile,
                                   dimension=dimension, exact_states=states,
                                   feasible_state_action_pairs=state_actions,
                                   one_float64_value_vector_gib=8 * states / 2 ** 30))
    return result


@njit(cache=True)
def scaled_policy(age, pipeline, theta, mu, cv, f, L):
    kind = int(theta[0])
    S = theta[1] * mu
    onhand, pipe = age.sum(), pipeline.sum()
    if kind == 0:
        return max(0., S - onhand - pipe)
    if kind == 1:
        return max(0., min(theta[2] * mu, S - onhand - pipe))
    if kind == 2:
        effective = 0.
        for i in range(len(age)):
            effective += age[i] * ((i + 1.) / len(age)) ** theta[3]
        return max(0., min(theta[2] * mu, S - effective - pipe))
    S2, b = theta[2] * mu, theta[3] * mu
    ip = onhand + pipe
    remaining = max(0., onhand - mu)
    waste0 = min(max(0., age[0] - f * mu), remaining)
    next_oldest = min(max(0., age[0] + age[1] - f * mu), remaining) - waste0
    next_onhand = remaining - waste0 + pipeline[0]
    waste1 = min(max(0., next_oldest - f * mu), max(0., next_onhand - mu))
    ew = waste0 + waste1
    if ip < b:
        return max(0., S - (1 - (S2 - S) / b) * ip + ew)
    return max(0., S2 - ip + ew)


def bounds_initial(kind, cap, mu, cbs=None):
    normalized_cap = cap / mu
    if kind == 0:
        return [(0., normalized_cap)], [0.6 * normalized_cap]
    if kind == 1:
        return [(0., normalized_cap), (0., normalized_cap)], [normalized_cap, .8]
    if kind == 2:
        # CBS is embedded at exponent=0; include its fitted point as the initial
        # point so this expanded class cannot be worse on the training sample.
        initial = [*cbs, 0.] if cbs is not None else [.6 * normalized_cap, .8, 1.]
        return [(0., normalized_cap), (0., normalized_cap), (0., 3.)], initial
    return [(0., normalized_cap), (0., normalized_cap), (.05, normalized_cap)], [2., 3., 2.5]


def paired_improvement(reference, candidate):
    reference, candidate = np.asarray(reference), np.asarray(candidate)
    diff = reference - candidate
    radius = float(stats.t.ppf(.975, len(diff) - 1) * stats.sem(diff))
    return dict(cost_reduction=float(diff.mean()), ci95=[float(diff.mean() - radius), float(diff.mean() + radius)],
                relative_reduction_percent=float(100 * diff.mean() / reference.mean()))


def run_one(item):
    scenario = Scenario(**item["scenario"])
    destination = OUT / f"{scenario.name}.json"
    if destination.exists():
        return json.loads(destination.read_text())
    tapes = {phase: sample_demands(scenario, x["paths"], x["burnin"] + x["horizon"], x["seed"])
             for phase, x in PROTOCOL.items() if isinstance(x, dict) and "paths" in x}
    def evaluate(kind, x, phase):
        return evaluate_kernel(scaled_policy, np.r_[float(kind), x], tapes[phase], scenario.m,
                               scenario.L, item["cap"], scenario.mean, scenario.cv, scenario.f,
                               scenario.h, scenario.p, scenario.w, PROTOCOL[phase]["burnin"])
    results = {}
    for kind, name in enumerate(PROTOCOL["policies"]):
        cbs = results.get("CBS", {}).get("theta")
        bounds, initial = bounds_initial(kind, item["cap"], scenario.mean, cbs)
        runs = [optimize(lambda x: evaluate(kind, x, "train")[0].mean(), bounds, initial,
                         PROTOCOL["optimizer_evaluations_per_start"], seed)
                for seed in PROTOCOL["optimizer_seeds"]]
        chosen = min(runs, key=lambda r: r["cost"])
        validation, _ = evaluate(kind, chosen["theta"], "validation")
        results[name] = dict(theta=chosen["theta"], optimizer_runs=runs,
                             training_cost=chosen["cost"], validation_cost=float(validation.mean()))
    selected = min(("age_discount", "BSP_low_EW"), key=lambda name: results[name]["validation_cost"])
    # All structures and parameters are now fixed before reading the diagnostic
    # holdout outputs. No main-experiment final-test tape is ever generated.
    for kind, name in enumerate(PROTOCOL["policies"]):
        result = results[name]
        costs, components = evaluate(kind, result["theta"], "diagnostic_holdout")
        result.update(holdout_cost=float(costs.mean()), path_costs=costs.tolist(),
                      mean_components=components.mean(axis=0).tolist())
    result = dict(**item, policies=results, selected_strong=selected,
                  vs_CBS=paired_improvement(results["CBS"]["path_costs"], results[selected]["path_costs"]),
                  vs_BSP=paired_improvement(results["BSP"]["path_costs"], results[selected]["path_costs"]))
    destination.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT / "protocol.json").write_text(json.dumps(dict(**PROTOCOL, source_sha256=source_hash), indent=2) + "\n")
    # Verify the FFT median calculation against the shared direct-convolution
    # implementation on all four primary cases before using it at larger scales.
    for cv in PROTOCOL["cv"]:
        for f in PROTOCOL["f"]:
            s = Scenario("cap_crosscheck", m=3, L=2, cv=cv, f=f)
            assert fast_cap(s)[0] == inventory_cap(s)
    items = grid()
    (OUT / "complexity.json").write_text(json.dumps(items, indent=2) + "\n")
    print(json.dumps([{k: r[k] for k in ("scenario", "cap", "exact_states", "one_float64_value_vector_gib")}
                      for r in items]), flush=True)
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = []
        for result in pool.map(run_one, items):
            results.append(result)
            print(json.dumps(dict(name=result["scenario"]["name"], strong=result["selected_strong"],
                                  vs_CBS=result["vs_CBS"], vs_BSP=result["vs_BSP"])), flush=True)
    summary = dict(protocol=PROTOCOL, seconds=time.perf_counter() - start, results=results)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
