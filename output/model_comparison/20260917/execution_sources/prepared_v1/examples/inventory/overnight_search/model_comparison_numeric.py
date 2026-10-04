"""Fresh-backbone numerical jobs; preserves every previous experiment unchanged.

The pure-policy action cache is exact, bounded, and enabled for all new phases.
Optimization records its literal start and warm starts, and final refitting can
retain coefficients learned during discovery instead of restarting blindly.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import differential_evolution
from scipy.stats import qmc

from .evaluator import NumericalSandbox, prelude
from .memory_guard import MemoryGuardMixin


def comparison_optimize(objective, bounds, initial, warm_starts, budget, seed):
    """Unit-box DE with an exact total objective-call cap and retained starts."""
    bounds = np.asarray(bounds, dtype=float).reshape((-1, 2))
    initial = np.asarray(initial, dtype=float)
    if len(bounds) != len(initial) or budget < 1:
        raise ValueError("Invalid optimization shape/budget")
    if np.any(~np.isfinite(bounds)) or np.any(bounds[:, 0] >= bounds[:, 1]):
        raise ValueError("Bounds must have positive finite widths")
    if np.any(initial < bounds[:, 0]) or np.any(initial > bounds[:, 1]):
        raise ValueError("Literal initial values fall outside bounds")
    start = time.monotonic()
    count, best, best_x = 0, float("inf"), initial.copy()
    initial_records = []

    class Exhausted(Exception):
        pass

    def call(x):
        nonlocal count, best, best_x
        if count >= budget:
            raise Exhausted()
        x = np.asarray(x, dtype=float)
        value = float(objective(x))
        count += 1
        if not np.isfinite(value):
            raise ValueError("Nonfinite objective")
        if value < best:
            best, best_x = value, x.copy()
        if count == 1 or count % 64 == 0:
            print("OPT_PROGRESS=" + json.dumps({"nfev": count, "best": best,
                  "elapsed_seconds": time.monotonic() - start}), flush=True)
        return value

    seeds = [initial]
    for x in warm_starts or []:
        x = np.asarray(x, dtype=float)
        if x.shape != initial.shape or np.any(~np.isfinite(x)):
            raise ValueError("Invalid warm start")
        x = np.clip(x, bounds[:, 0], bounds[:, 1])
        if not any(np.array_equal(x, previous) for previous in seeds):
            seeds.append(x)
    for index, x in enumerate(seeds):
        if count >= budget:
            break
        initial_records.append({"kind": "literal" if index == 0 else "warm",
                                "theta": x.tolist(), "cost": call(x)})
    dimension = len(initial)
    population_size = min(128, max(16, 4 * dimension))
    if dimension and count < budget:
        width = bounds[:, 1] - bounds[:, 0]
        population = qmc.LatinHypercube(d=dimension, seed=seed).random(population_size)
        ranked = sorted(initial_records, key=lambda r: r["cost"])
        for index, record in enumerate(ranked[:population_size]):
            population[index] = (np.asarray(record["theta"]) - bounds[:, 0]) / width

        def unit_objective(unit):
            return call(bounds[:, 0] + width * unit)

        try:
            differential_evolution(unit_objective, [(0., 1.)] * dimension,
                                   init=population, maxiter=budget,
                                   mutation=(.4, 1.), recombination=.8,
                                   rng=seed, polish=False, tol=0., atol=0.)
        except Exhausted:
            pass
    return {"theta": best_x.tolist(), "cost": best, "nfev": count,
            "seconds": time.monotonic() - start, "population_size": population_size,
            "starts": initial_records, "optimizer_revision": "unit_box_warm_de_v1"}


def comparison_worker(job):
    # These helpers are installed by the trusted sandbox prelude.
    prepared = prepare_policy(job["code"], None)
    namespace = {}
    exec(compile(prepared["source"], "candidate.py", "exec"), namespace)
    numeric = njit(namespace["compute_order_amount"], boundscheck=True)

    @njit
    def policy(age, pipeline, theta, mu, cv, f, L):
        return numeric(age, pipeline, mu, cv, f, L, theta)

    bounds = [[x["min"], x["max"]] for x in prepared["opt_params"].values()]
    initial = prepared["values"]
    outputs = {}
    for spec in job["scenarios"]:
        scenario = Scenario(**spec)
        seed = job.get("scenario_seeds", {}).get(scenario.name, job["seed"])
        tape = sample_demands(scenario, job["paths"], job["burnin"] + job["horizon"], seed)
        tape_hash = hashlib.sha256(tape.tobytes(order="C")).hexdigest()
        counters = {"hits": 0, "misses": 0, "peak_entries": 0, "evaluations": 0}
        print("SCENARIO_START=" + json.dumps({"name": scenario.name}), flush=True)

        def score(theta):
            if job.get("cache_actions", True):
                result = cached_evaluate(scenario, tape, policy, theta, job["burnin"],
                                         audit=job.get("audit_actions", False))
                counters["hits"] += int(result[2])
                counters["misses"] += int(result[3])
                counters["peak_entries"] = max(counters["peak_entries"], int(result[4]))
                costs, metrics = result[:2]
            else:
                costs, metrics = evaluate_kernel(policy, np.asarray(theta, dtype=float), tape,
                    scenario.m, scenario.L, inventory_cap(scenario), scenario.mean,
                    scenario.sd/scenario.mean, scenario.f, scenario.h, scenario.p,
                    scenario.w, job["burnin"])
            counters["evaluations"] += 1
            return costs, metrics

        if job["op"] == "fit":
            record = comparison_optimize(lambda theta: score(theta)[0].mean(), bounds,
                initial, job.get("warm_starts", {}).get(scenario.name, []),
                job["budget"], job["optimizer_seed"])
        elif job["op"] == "evaluate":
            record = {"theta": job["theta"][scenario.name], "nfev": 0}
        else:
            raise ValueError("Unknown numerical operation")
        costs, metrics = score(record["theta"])
        record.update(cost=float(costs.mean()), path_costs=costs.tolist(),
                      metrics=metrics.mean(axis=0).tolist(), cap=inventory_cap(scenario),
                      demand_sha256=tape_hash, demand_seed=int(seed),
                      cache_actions=bool(job.get("cache_actions", True)),
                      action_cache=counters,
                      transitions=counters["evaluations"] * job["paths"] *
                                  (job["burnin"] + job["horizon"]))
        outputs[scenario.name] = record
        print("SCENARIO_FINISHED=" + json.dumps({"name": scenario.name,
              "nfev": record["nfev"], "cost": record["cost"]}), flush=True)
    return {"results": outputs, "parameters": prepared["opt_params"],
            "code_sha256": prepared["code_sha256"],
            "structure_sha256": prepared["structure_sha256"],
            "import_normalization": prepared.get("import_normalization", []),
            "transitions": sum(r["transitions"] for r in outputs.values()),
            "execution_revision": "model_comparison_numeric_v1"}


class ComparisonSandbox(MemoryGuardMixin, NumericalSandbox):
    memory_limit_bytes = 1024 ** 3


def evaluate_comparison(job, timeout=3600, log_path=None):
    """Return a complete record or an explicit, measured failure record."""
    trusted = (prelude() + "\n" + inspect.getsource(comparison_optimize) +
               "\n" + inspect.getsource(comparison_worker))
    source = trusted + "\njob = " + repr(job) + (
        '\nprint("COMPARISON_RESULT="+json.dumps(comparison_worker(job),allow_nan=False),flush=True)\n')
    started = time.monotonic()
    result = ComparisonSandbox(sys.executable).run(source, timeout_seconds=timeout,
                                                   max_output_bytes=8_000_000)
    metadata = {"wall_seconds": time.monotonic() - started,
                "worker_seconds": result.elapsed_seconds,
                "peak_rss_bytes": result.observed_peak_rss_bytes,
                "timeout_seconds": timeout,
                "trusted_source_sha256": hashlib.sha256(trusted.encode()).hexdigest(),
                "request_sha256": hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()}
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**metadata, **result.to_dict()}, ensure_ascii=False, indent=2))
    lines = result.stdout.splitlines()
    if result.returncode == 0 and not result.timed_out and not result.memory_guard_exceeded:
        for line in reversed(lines):
            if line.startswith("COMPARISON_RESULT="):
                return {**json.loads(line.split("=", 1)[1]), **metadata, "valid": True}
    progress = []
    for line in lines:
        if line.startswith(("SCENARIO_START=", "SCENARIO_FINISHED=", "OPT_PROGRESS=")):
            try:
                kind, value = line.split("=", 1)
                progress.append({"kind": kind, **json.loads(value)})
            except (ValueError, json.JSONDecodeError):
                pass
    return {**metadata, "valid": False,
            "error_type": "memory" if result.memory_guard_exceeded else
                          "timeout" if result.timed_out else "worker_error",
            "error": result.stderr[-6000:], "progress": progress}
