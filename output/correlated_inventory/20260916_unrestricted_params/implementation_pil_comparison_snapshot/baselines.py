"""Train-only classical and conditional projected-inventory baselines.

PIL uses a fixed scrambled Sobol sample of *joint conditional demand paths*.
Each path uses the exact lost-sales inventory recursion; averaging inventory
before applying the positive part is deliberately not used. Conditional AR(1)
paths are interpolated on a fine latent-state grid. Thus the numerical policy
is a deterministic approximation, not an exact conditional expectation.

For random quoted lead times, ordinary PIL projects only committed arrivals.
``pil_cop_continuation`` additionally projects subsequent constant orders at the
training-fitted COP rate, including independent future quotes and overtaking.
Neither extension is asserted to be the canonical fixed-lead PIL policy.
"""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
import hashlib
import json
import math
from time import perf_counter

import numpy as np
from numba import njit
from scipy.optimize import differential_evolution, minimize, minimize_scalar
from scipy.special import log_ndtr, ndtri
from scipy.stats import qmc

from .data import Scenario, validate_tapes
from .environment import simulate_compiled, simulate_callable

VERSION = "conditional-pil-baselines-v1"
NAMES = ("constant_order", "base_stock", "capped_base_stock", "forecast_capped_base_stock",
         "conditional_pil", "forecast_adaptive_pil", "pil_cop_continuation")
MODES = {name: i for i, name in enumerate(NAMES)}
PARAMETERS = {
    "constant_order": ("q_over_mean",),
    "base_stock": ("S_over_mean",),
    "capped_base_stock": ("S_over_mean", "cap_over_mean"),
    "forecast_capped_base_stock": ("S_over_mean", "cap_over_mean", "target_forecast_gain", "cap_forecast_gain"),
    "conditional_pil": ("S_over_mean",),
    "forecast_adaptive_pil": ("S_over_mean", "cap_over_mean", "target_forecast_gain", "cap_forecast_gain", "inventory_gain"),
    "pil_cop_continuation": ("S_over_mean", "continuation_q_over_mean"),
}


def _scenario_key(scenario):
    return json.dumps(asdict(scenario), sort_keys=True)


@lru_cache(maxsize=48)
def _forecast_bank_cached(scenario_key, inner_paths, seed, grid_step):
    scenario = Scenario(**json.loads(scenario_key))
    n = int(inner_paths)
    if n < 2 or n & (n - 1):
        raise ValueError("inner_paths must be a power of two >= 2")
    if not 0 < grid_step <= 0.25:
        raise ValueError("grid_step must be in (0, .25]")
    k = scenario.max_lead_time + 1
    uniforms = qmc.Sobol(3 * k, scramble=True, seed=int(seed)).random_base2(int(math.log2(n)))
    uniforms = np.clip(uniforms, np.finfo(float).tiny, np.nextafter(1.0, 0.0))
    mu = scenario.mean_demand
    process = scenario.demand_process
    rho = scenario.rho_latent
    if process == "ar1" and rho != 0:
        z_grid = np.linspace(-12.0, 12.0, int(round(24.0 / grid_step)) + 1)
        signal_grid = -mu * log_ndtr(-z_grid)
        innovations = ndtri(uniforms[:, :k])
        paths = np.empty((len(z_grid), n, k), dtype=np.float64)
        means = np.empty((len(z_grid), k), dtype=np.float64)
        # Gaussian quadrature computes conditional means independently of QMC.
        nodes, weights = np.polynomial.hermite.hermgauss(40)
        weights = weights / math.sqrt(math.pi)
        for g, initial_z in enumerate(z_grid):
            z = np.full(n, initial_z)
            for j in range(k):
                z = rho * z + math.sqrt(1.0 - rho * rho) * innovations[:, j]
                paths[g, :, j] = -mu * log_ndtr(-z)
                power = rho ** (j + 1)
                values = power * initial_z + math.sqrt(2.0 * (1.0 - power * power)) * nodes
                means[g, j] = float(np.dot(weights, -mu * log_ndtr(-values)))
        process_code = 1
    elif process == "regime" and scenario.regime_p_stay != 0.5:
        signal_grid = np.array([0.0, mu * math.log(2.0)])
        paths = np.empty((2, n, k), dtype=np.float64)
        means = np.empty((2, k), dtype=np.float64)
        for initial_state in (0, 1):
            state = np.full(n, initial_state, dtype=np.int64)
            for j in range(k):
                state = (state + (uniforms[:, j] >= scenario.regime_p_stay)) % 2
                u = (state + uniforms[:, k + j]) / 2.0
                paths[initial_state, :, j] = -mu * np.log1p(-u)
                means[initial_state, j] = mu * (1.0 + (2 * initial_state - 1) * math.log(2.0)
                                               * (2.0 * scenario.regime_p_stay - 1.0) ** (j + 1))
        process_code = 2
    else:
        signal_grid = np.array([0.0])
        paths = (-mu * np.log1p(-uniforms[:, :k]))[None, :, :]
        means = np.full((1, k), mu)
        process_code = 0
    # Arrivals at j=1,...,M-1 from constant orders placed at times 1,...,M-1.
    # The current order is excluded. Counts share demand paths' Sobol rows.
    continuation_counts = np.zeros((n, k), dtype=np.float64)
    lead_cdf = np.cumsum(scenario.lead_time_probabilities)
    lead_values = np.asarray(scenario.lead_time_values)
    for placed in range(1, k):
        quotes = lead_values[np.searchsorted(lead_cdf, uniforms[:, 2 * k + placed - 1], side="right")]
        due = placed + quotes
        for sample in range(n):
            if due[sample] < k:
                continuation_counts[sample, due[sample]] += 1.0
    arrays = (np.ascontiguousarray(signal_grid), np.ascontiguousarray(paths),
              np.ascontiguousarray(means), np.ascontiguousarray(continuation_counts))
    for arr in arrays:
        arr.setflags(write=False)
    return (process_code, *arrays)


def forecast_bank(scenario, inner_paths=128, seed=81173, grid_step=0.05):
    return _forecast_bank_cached(_scenario_key(scenario), int(inner_paths), int(seed), float(grid_step))


@njit(cache=True)
def _signal_bracket(last_demand, process_code, signal_grid):
    if process_code == 0:
        return 0, 0, 0.0
    if process_code == 2:
        i = 1 if last_demand >= signal_grid[1] else 0
        return i, i, 0.0
    if last_demand <= signal_grid[0]:
        return 0, 0, 0.0
    if last_demand >= signal_grid[-1]:
        i = len(signal_grid) - 1
        return i, i, 0.0
    hi = int(np.searchsorted(signal_grid, last_demand))
    lo = hi - 1
    return lo, hi, (last_demand - signal_grid[lo]) / (signal_grid[hi] - signal_grid[lo])


@njit(cache=True)
def _residual_from_paths(inventory, pipeline, quote, lo, hi, weight, demand_paths,
                         continuation_counts, continuation_order):
    """Exact lost-sales recursion for each numerical conditional sample path."""
    total = 0.0
    count = demand_paths.shape[1]
    for sample in range(count):
        stock = inventory
        for j in range(quote):
            if j > 0:
                stock += pipeline[j - 1] + continuation_order * continuation_counts[sample, j]
            demand = demand_paths[lo, sample, j]
            if hi != lo:
                demand += weight * (demand_paths[hi, sample, j] - demand)
            stock = max(0.0, stock - demand)
        # At the quoted arrival epoch, the order being chosen joins any older
        # order or future continuation order due that same day. Include those
        # other arrivals before computing this order's replenishment gap.
        if quote - 1 < len(pipeline):
            stock += pipeline[quote - 1]
        if quote < continuation_counts.shape[1]:
            stock += continuation_order * continuation_counts[sample, quote]
        total += stock
    return total / count


@njit(cache=True)
def _order_numeric(mode, theta, inventory, pipeline, last_demand, quote,
                   mu, mean_lead, process_code, signal_grid, demand_paths, means, continuation_counts):
    if mode == 0:
        return mu * theta[0]
    position = inventory
    for value in pipeline:
        position += value
    if mode == 1:
        return max(0.0, mu * theta[0] - position)
    if mode == 2:
        return min(mu * theta[1], max(0.0, mu * theta[0] - position))
    lo, hi, weight = _signal_bracket(last_demand, process_code, signal_grid)
    arrival_mean = means[lo, quote] + weight * (means[hi, quote] - means[lo, quote])
    if mode == 3:
        forecast_sum = 0.0
        for j in range(quote + 1):
            forecast_sum += means[lo, j] + weight * (means[hi, j] - means[lo, j])
        target = max(0.0, mu * theta[0] + theta[2] * (forecast_sum - (mean_lead + 1.0) * mu))
        cap = max(0.0, mu * theta[1] + theta[3] * (arrival_mean - mu))
        return min(cap, max(0.0, target - position))
    continuation = mu * theta[1] if mode == 6 else 0.0
    if process_code == 0 and quote == 1:
        # Analytic one-period exponential check, before any future order arrives.
        projected = inventory + mu * math.expm1(-inventory / mu)
        if len(pipeline) > 0:
            projected += pipeline[0]
    else:
        projected = _residual_from_paths(inventory, pipeline, quote, lo, hi, weight,
                                         demand_paths, continuation_counts, continuation)
    if mode == 5:
        target = max(0.0, mu * theta[0] + theta[2] * (arrival_mean - mu))
        cap = max(0.0, mu * theta[1] + theta[3] * (arrival_mean - mu))
        return min(cap, max(0.0, target - theta[4] * projected))
    return max(0.0, mu * theta[0] - projected)


def _numeric_policy(name, scenario, bank):
    mode = MODES[name]
    mu, mean_lead = scenario.mean_demand, scenario.mean_lead_time
    process_code, signal_grid, paths, means, continuation = bank

    @njit
    def policy(inventory, pipeline, last_demand, quote, theta):
        return _order_numeric(mode, theta, inventory, pipeline, last_demand, quote, mu, mean_lead,
                              process_code, signal_grid, paths, means, continuation)
    return policy


def make_policy(record, *, compiled=True, inner_paths=None, grid_step=None):
    """Reconstruct a frozen stationary callable without data or model access."""
    scenario = Scenario(**record["scenario"])
    n = int(record["forecast"]["inner_paths"] if inner_paths is None else inner_paths)
    step = float(record["forecast"]["grid_step"] if grid_step is None else grid_step)
    bank = forecast_bank(scenario, n, record["forecast"]["seed"], step)
    numeric = _numeric_policy(record["name"], scenario, bank)
    theta = np.asarray(record["theta"], dtype=np.float64)
    expected = len(PARAMETERS[record["name"]])
    if theta.shape != (expected,) or not np.isfinite(theta).all():
        raise ValueError("Invalid frozen parameter vector")
    theta.setflags(write=False)

    @njit
    def frozen(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
        return numeric(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time, theta)
    if compiled:
        return frozen

    def scalar(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
        return _order_numeric.py_func(MODES[record["name"]], theta, float(on_hand_inventory),
            np.asarray(pipeline_orders, dtype=float), float(last_demand), int(quoted_lead_time),
            scenario.mean_demand, scenario.mean_lead_time, *bank)
    return scalar


def evaluate(record, tapes, *, horizon, burnin, compiled=True, inner_paths=None, return_trace=False):
    scenario = Scenario(**record["scenario"])
    policy = make_policy(record, compiled=compiled, inner_paths=inner_paths)
    runner = simulate_compiled if compiled else simulate_callable
    return runner(policy, tapes, scenario, horizon, burnin, return_trace=return_trace)


def evaluate_baseline(record, tapes, scenario=None, *, horizon=500, burnin=500,
                      return_trace=False, compiled=True):
    """Public orchestration alias; a supplied scenario must match the record."""
    if scenario is not None and Scenario(**record["scenario"]) != scenario:
        raise ValueError("Frozen baseline scenario differs from evaluation scenario")
    return evaluate(record, tapes, horizon=horizon, burnin=burnin,
                    compiled=compiled, return_trace=return_trace)


_parameterized_kernel = None


def _get_parameterized_kernel():
    global _parameterized_kernel
    if _parameterized_kernel is None:
        from .fast_policy import parameterized_kernel_source
        namespace = {"np": np, "math": math}
        exec(parameterized_kernel_source(), namespace)
        _parameterized_kernel = njit(namespace["simulate_kernel_parameterized"])
    return _parameterized_kernel


def _make_objective(name, scenario, tapes, horizon, burnin, bank):
    numeric = _numeric_policy(name, scenario, bank)
    kernel = _get_parameterized_kernel()
    def per_path(theta):
        values = kernel(numeric, tapes["demands"], tapes["lead_times"], tapes["initial_last_demand"],
                        scenario.max_lead_time, scenario.holding_cost, scenario.lost_sales_cost,
                        int(horizon), int(burnin), False, np.asarray(theta, dtype=np.float64))
        return (values[0] + values[1]) / horizon
    def objective(theta):
        return float(per_path(theta).mean())
    return objective, per_path


def _bounds(name, scenario):
    level = 2.5 * (scenario.mean_lead_time + 1)
    return {
        "constant_order": [(0.0, 1.5)],
        "base_stock": [(0.0, level)],
        "capped_base_stock": [(0.0, level), (0.0, 2.5)],
        "forecast_capped_base_stock": [(0.0, level), (0.0, 3.0), (-1.0, 2.5), (-1.0, 3.0)],
        "conditional_pil": [(0.0, 3.0)],
        "forecast_adaptive_pil": [(0.0, 3.0), (0.0, 3.0), (-1.0, 3.0), (-1.0, 3.0), (0.0, 2.0)],
        "pil_cop_continuation": [(0.0, 3.0)],
    }[name]


def _optimize(objective, bounds, anchors, seed, *, strong=True):
    """Search distinct starts and expand active artificial boundaries twice."""
    best = None
    evaluations = 0
    rounds = []
    cache = {}
    def score(theta):
        nonlocal evaluations, best
        key = tuple(float(x) for x in theta)
        if key not in cache:
            value = objective(np.asarray(key))
            if not math.isfinite(value):
                raise ValueError("Nonfinite training objective")
            cache[key] = value
            evaluations += 1
            if best is None or value < best[0]:
                best = (value, np.asarray(key))
        return cache[key]
    current = np.asarray(bounds, dtype=float)
    for expansion in range(3):
        candidates = [np.clip(np.asarray(x), current[:, 0], current[:, 1]) for x in anchors]
        if len(current) == 1:
            grid = np.linspace(*current[0], 33 if strong else 17)
            values = np.array([score([x]) for x in grid])
            for idx in np.argsort(values)[:3]:
                left, right = grid[max(0, idx - 1)], grid[min(len(grid) - 1, idx + 1)]
                if left < right:
                    result = minimize_scalar(lambda x: score([x]), bounds=(left, right), method="bounded",
                                             options={"xatol": 2e-4, "maxiter": 50})
                    candidates.append(np.array([result.x]))
        else:
            for point in candidates:
                score(point)
            result = differential_evolution(score, current, seed=seed + expansion, popsize=7 if strong else 4,
                maxiter=(24 if len(current) <= 2 else 18) if strong else 4,
                tol=2e-4, atol=0.0, polish=False, workers=1, updating="immediate")
            candidates.append(result.x)
            candidates.extend(np.asarray(x) for x in sorted(cache, key=cache.get)[:3])
            for start in candidates[:4 if strong else 2]:
                start = np.clip(start, current[:, 0], current[:, 1])
                result = minimize(score, start, method="Powell", bounds=current,
                    options={"maxfev": 220 if strong else 55, "xtol": 5e-4, "ftol": 1e-5})
                score(result.x)
        for point in candidates:
            score(point)
        lower_edge = best[1] <= current[:, 0] + 0.005 * (current[:, 1] - current[:, 0])
        upper_edge = best[1] >= current[:, 1] - 0.005 * (current[:, 1] - current[:, 0])
        # Zero lower bounds are physical, negative lower bounds are artificial.
        active = upper_edge | (lower_edge & (current[:, 0] < 0))
        rounds.append({"bounds": current.tolist(), "best_theta": best[1].tolist(),
                       "mean_training_cost_per_period": best[0], "artificial_edge": active.tolist()})
        if not active.any():
            break
        for j in range(len(current)):
            width = current[j, 1] - current[j, 0]
            if upper_edge[j]:
                current[j, 1] += width
            if lower_edge[j] and current[j, 0] < 0:
                current[j, 0] -= width
    return best[1], best[0], {"evaluations": evaluations, "rounds": rounds,
        "unresolved_artificial_boundary": bool(active.any()), "seed": seed,
        "algorithm": "1D coarse grid + 3 bounded local searches; multidimensional DE + multistart Powell"}


def fit_baselines(train_tapes, scenario, *, horizon=200, burnin=500, inner_paths=128,
                  forecast_seed=81173, seed=51017, grid_step=0.05, strong=True,
                  names=None, convergence=True, existing=None, progress=None):
    """Fit using supplied training tapes only; return JSON-serializable records.

    No validation/test tape is accepted. ``existing`` supplies already-frozen
    prerequisites when resuming; each record's training fingerprint is checked.
    The 64/128/256/1024 QMC comparison reuses training paths and frozen theta.
    Final numerical resolution is chosen before external evaluation.
    """
    tapes = validate_tapes(train_tapes, scenario)
    if (isinstance(horizon, bool) or not isinstance(horizon, (int, np.integer)) or horizon < 1
            or isinstance(burnin, bool) or not isinstance(burnin, (int, np.integer)) or burnin < 0):
        raise ValueError("horizon must be a positive integer and burnin a nonnegative integer")
    if burnin + horizon > tapes["demands"].shape[1]:
        raise ValueError("Training tape shorter than requested window")
    fingerprint = hashlib.sha256()
    for key in ("demands", "lead_times", "initial_last_demand"):
        fingerprint.update(np.ascontiguousarray(tapes[key]).tobytes())
    training_hash = fingerprint.hexdigest()
    records = dict(existing or {})
    for record in records.values():
        if record["training"]["tape_sha256"] != training_hash:
            raise ValueError("Existing record used different training tapes")
        if (Scenario(**record["scenario"]) != scenario
                or record["training"]["horizon"] != horizon
                or record["training"]["burnin"] != burnin
                or record["version"] != VERSION):
            raise ValueError("Existing baseline has a different scenario, training window, or version")
    requested = tuple(names or NAMES)
    if set(requested) - set(NAMES):
        raise ValueError("Unknown baseline name")
    bank = forecast_bank(scenario, inner_paths, forecast_seed, grid_step)
    for index, name in enumerate(NAMES):
        if name not in requested or name in records:
            continue
        if name == "pil_cop_continuation" and "constant_order" not in records:
            raise ValueError("COP continuation requires a training-fitted constant_order record")
        started = perf_counter()
        if progress:
            progress({"event": "baseline_fit_started", "scenario": scenario.scenario_id, "name": name})
        objective, per_path = _make_objective(name, scenario, tapes, horizon, burnin, bank)
        cop_q = records.get("constant_order", {}).get("theta", [0.8])[0]
        if name == "constant_order":
            anchors = [[0.6], [0.8], [1.0]]
        elif name == "base_stock":
            anchors = [[scenario.mean_lead_time + 1]]
        elif name in {"capped_base_stock", "forecast_capped_base_stock"}:
            bs = records.get("base_stock", {}).get("theta", [scenario.mean_lead_time + 1])[0]
            previous = records.get("capped_base_stock", {}).get("theta", [bs, cop_q])
            anchors = [previous, [bs, 2.5], [bs, cop_q]]
            if name == "forecast_capped_base_stock":
                anchors = [list(x) + [0.0, 0.0] for x in anchors] + [list(previous) + [1.0, 1.0]]
        elif name == "conditional_pil":
            anchors = [[0.8], [1.0], [1.5]]
        elif name == "forecast_adaptive_pil":
            target = records.get("conditional_pil", {}).get("theta", [1.0])[0]
            anchors = [[target, 3.0, 0.0, 0.0, 1.0], [target, 1.2, 1.0, 0.0, 1.0],
                       [cop_q, cop_q, 0.0, 0.0, 0.0]]
        else:
            anchors = [[records.get("conditional_pil", {}).get("theta", [1.0])[0]]]
            full_objective = objective
            objective = lambda x: full_objective(np.array([x[0], cop_q]))
        bounds = _bounds(name, scenario)
        if bank[0] == 0 and name in {"forecast_capped_base_stock", "forecast_adaptive_pil"}:
            # Analytically zero forecast effects must not manufacture optimizer
            # boundary warnings or consume search on unidentifiable dimensions.
            active = ([0, 1] if len(scenario.lead_time_values) == 1 else [0, 1, 2]) if name == "forecast_capped_base_stock" else [0, 1, 4]
            full_objective = objective
            def expand(x):
                full = np.zeros(len(bounds), dtype=float)
                full[active] = x
                return full
            reduced = lambda x: full_objective(expand(x))
            reduced_theta, train_cost, search = _optimize(reduced, [bounds[j] for j in active],
                [np.asarray(x)[active] for x in anchors], seed + index, strong=strong)
            theta = expand(reduced_theta)
            search["active_parameter_indices"] = active
            search["analytic_reduction"] = "iid conditional demand means are exactly unconditional"
            # Preserve full-dimensional bounds for any later numerical refine.
            search["full_parameter_bounds"] = bounds
        else:
            theta, train_cost, search = _optimize(objective, bounds, anchors,
                                                 seed + index, strong=strong)
        if name == "pil_cop_continuation":
            theta = np.array([theta[0], cop_q])
        # Exact constant-order embedding avoids weakening CBS through finite bounds.
        if name == "capped_base_stock":
            embedding_periods = max(10000, burnin + horizon + 1)
            constant_embedding = np.array([embedding_periods * cop_q, cop_q])
            cost = objective(constant_embedding)
            if cost < train_cost:
                theta, train_cost = constant_embedding, cost
                search["selected_constant_order_embedding"] = True
            search["constant_order_embedding_cost"] = cost
            search["constant_order_embedding_guaranteed_periods"] = embedding_periods
            search["embedding_scope"] = "finite trajectory from zero inventory, not an infinite-horizon equivalence"
        if name == "forecast_capped_base_stock" and "capped_base_stock" in records:
            embedded = np.array(records["capped_base_stock"]["theta"] + [0.0, 0.0])
            embedded_cost = objective(embedded)
            search["capped_base_stock_embedding_cost"] = embedded_cost
            if embedded_cost < train_cost:
                theta, train_cost = embedded, embedded_cost
                search["selected_capped_base_stock_embedding"] = True
        if name == "forecast_adaptive_pil":
            # q=constant is exactly embedded by g=a=b=0, target=cap=q.
            embedded = np.array([cop_q, cop_q, 0.0, 0.0, 0.0])
            embedded_cost = objective(embedded)
            search["constant_order_embedding_cost"] = embedded_cost
            if embedded_cost < train_cost:
                theta, train_cost = embedded, embedded_cost
                search["selected_constant_order_embedding"] = True
            if "conditional_pil" in records:
                pil_target = records["conditional_pil"]["theta"][0]
                embedded = np.array([pil_target, pil_target, 0.0, 0.0, 1.0])
                embedded_cost = objective(embedded)
                search["conditional_pil_embedding_cost"] = embedded_cost
                if embedded_cost < train_cost:
                    theta, train_cost = embedded, embedded_cost
                    search["selected_conditional_pil_embedding"] = True
        record = {"name": name, "version": VERSION, "scenario": asdict(scenario),
            "theta": theta.tolist(), "parameters": dict(zip(PARAMETERS[name], map(float, theta))),
            "forecast": {"inner_paths": int(inner_paths), "seed": int(forecast_seed), "grid_step": float(grid_step),
                         "latent_grid_limits": [-12.0, 12.0], "conditional_means": "analytic iid/regime; 40-node Gaussian quadrature AR1",
                         "conditional_paths": "fixed scrambled Sobol; AR signal interpolation",
                         "same_day_other_arrivals_included": True},
            "training": {"tape_sha256": training_hash, "n_paths": len(tapes["demands"]),
                         "horizon": horizon, "burnin": burnin, "mean_cost_per_period": float(train_cost)},
            "search": search,
            "random_lead_interpretation": "committed-only projection" if name in {"conditional_pil", "forecast_adaptive_pil"}
                else "committed arrivals plus future constant-order continuation with independently sampled quotes" if name == "pil_cop_continuation"
                else "inventory-position rule with all publicly known outstanding arrivals",
            "formula": _formula(name)}
        if convergence and name in {"conditional_pil", "forecast_adaptive_pil", "pil_cop_continuation"}:
            checks = {}
            for n in (64, 128, 256, 1024):
                _, get_paths = _make_objective(name, scenario, tapes, horizon, burnin,
                    forecast_bank(scenario, n, forecast_seed, grid_step))
                checks[n] = get_paths(theta)
            reference = checks[1024]
            reference_mean = float(reference.mean())
            convergence_rows = []
            selected = 1024
            for n in (64, 128, 256, 1024):
                delta = checks[n] - reference
                mean_gap = abs(float(delta.mean())) / max(reference_mean, 1e-12)
                path_gap = float(np.abs(delta).mean()) / max(reference_mean, 1e-12)
                convergence_rows.append({"inner_paths": n, "mean_cost_per_period": float(checks[n].mean()),
                    "relative_mean_gap_vs_1024": mean_gap, "relative_mean_abs_path_gap_vs_1024": path_gap})
                if n >= inner_paths and mean_gap <= 0.001 and path_gap <= 0.005 and selected == 1024:
                    selected = n
            record["forecast"]["inner_paths"] = selected
            record["training"]["mean_cost_per_period"] = float(checks[selected].mean())
            record["qmc_convergence"] = {"rows": convergence_rows, "selected_inner_paths": selected,
                "rule": "smallest N >= fit N with training mean gap <=0.1% and mean absolute paired path gap <=0.5% versus N=1024",
                "theta_refit": False, "scope": "numerical resolution of frozen policy on training paths; not external validation"}
            if selected > inner_paths:
                refinements = []
                for refinement_pass in range(2):
                    final_objective, final_paths = _make_objective(name, scenario, tapes, horizon, burnin,
                        forecast_bank(scenario, selected, forecast_seed, grid_step))
                    before_cost = final_objective(theta)
                    refine_bounds = np.asarray(search.get("full_parameter_bounds", search["rounds"][-1]["bounds"]))
                    if name == "pil_cop_continuation":
                        fun = lambda x: final_objective(np.array([x[0], cop_q]))
                        start = theta[:1]
                    else:
                        fun, start = final_objective, theta
                    # An explicitly evaluated nested-family anchor may sit
                    # outside the original search box. Include the incumbent.
                    refine_bounds[:, 0] = np.minimum(refine_bounds[:, 0], start)
                    refine_bounds[:, 1] = np.maximum(refine_bounds[:, 1], start)
                    refined = minimize(fun, start, method="Powell", bounds=refine_bounds,
                        options={"maxfev": 250 if strong else 70, "xtol": 3e-4, "ftol": 1e-6})
                    if name == "pil_cop_continuation":
                        proposed = np.array([refined.x[0], cop_q])
                    else:
                        proposed = refined.x
                    after_cost = final_objective(proposed)
                    if after_cost < before_cost:
                        theta = proposed
                    selected_paths = final_paths(theta)
                    _, reference_paths = _make_objective(name, scenario, tapes, horizon, burnin,
                        forecast_bank(scenario, 1024, forecast_seed, grid_step))
                    reference = reference_paths(theta)
                    delta = selected_paths - reference
                    scale = max(float(reference.mean()), 1e-12)
                    mean_gap = abs(float(delta.mean())) / scale
                    path_gap = float(np.abs(delta).mean()) / scale
                    refinements.append({"inner_paths": selected, "before_cost": before_cost,
                        "after_cost": float(selected_paths.mean()), "function_evaluations": int(refined.nfev),
                        "relative_mean_gap_vs_1024": mean_gap,
                        "relative_mean_abs_path_gap_vs_1024": path_gap})
                    if selected == 1024 or (mean_gap <= .001 and path_gap <= .005):
                        break
                    selected = 1024
                record["theta"] = theta.tolist()
                record["parameters"] = dict(zip(PARAMETERS[name], map(float, theta)))
                record["forecast"]["inner_paths"] = selected
                record["training"]["mean_cost_per_period"] = float(selected_paths.mean())
                record["qmc_convergence"].update(theta_refit=True, selected_inner_paths=selected,
                    refinement=refinements, rows_scope="before refitting at upgraded numerical resolution")
        record["fit_seconds"] = perf_counter() - started
        records[name] = record
        if progress:
            progress({"event": "baseline_fit_completed", "scenario": scenario.scenario_id, "name": name,
                      "train_cost_per_period": record["training"]["mean_cost_per_period"],
                      "seconds": record["fit_seconds"], "record": record})
    return records


def _formula(name):
    return {
      "constant_order": "q=mu*c",
      "base_stock": "q=[mu*S-I-sum(P)]+",
      "capped_base_stock": "q=min(mu*C,[mu*S-I-sum(P)]+)",
      "forecast_capped_base_stock": "q=min([mu*C+b*(m_arrival-mu)]+,[mu*S+a*(sum(m_0..m_L)-(E[L]+1)*mu)-I-sum(P)]+)",
      "conditional_pil": "q=[mu*S-E_QMC[I immediately before current order arrives]]+; only committed arrivals",
      "forecast_adaptive_pil": "q=min([mu*C+b*(m_arrival-mu)]+,[mu*S+a*(m_arrival-mu)-g*E_QMC[I_before_arrival]]+)",
      "pil_cop_continuation": "q=[mu*S-E_QMC[I_before_arrival with future q_COP orders and independent future quotes]]+",
    }[name]
