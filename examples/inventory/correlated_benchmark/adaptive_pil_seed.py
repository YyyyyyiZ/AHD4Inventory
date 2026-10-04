"""Expose a frozen Adaptive PIL as editable policy source and trusted forecasts.

The policy source contains the entire five-parameter decision rule. Only its
conditional numerical forecasts live in two injected helpers. The helpers use
the frozen baseline's QMC bank and have no access to tapes, clocks, previous
calls, credentials, or candidate coefficients. This module does not change the
original benchmark, baseline, evaluator, or running evolution code.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math

import numpy as np
from numba import njit

from . import baselines
from .data import Scenario


VERSION = "adaptive-pil-editable-seed-v1"
HELPER_NAMES = ("conditional_projected_inventory", "conditional_arrival_mean")
ARRAY_NAMES = ("signal_grid", "demand_paths", "means", "continuation_counts")
PARAMETER_NAMES = baselines.PARAMETERS["forecast_adaptive_pil"]


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _validate_record(record):
    if record.get("name") != "forecast_adaptive_pil":
        raise ValueError("The initial rule must be a frozen forecast_adaptive_pil record")
    if record.get("version") != baselines.VERSION:
        raise ValueError("Unsupported frozen baseline version")
    scenario = Scenario(**record["scenario"])
    theta = np.asarray(record["theta"], dtype=np.float64)
    if theta.shape != (5,) or not np.isfinite(theta).all():
        raise ValueError("Adaptive PIL requires its five finite frozen coefficients")
    forecast = record["forecast"]
    if list(forecast.get("latent_grid_limits", [-12.0, 12.0])) != [-12.0, 12.0]:
        raise ValueError("Unsupported latent forecast grid limits")
    if len(scenario.lead_time_values) > 1 and not forecast.get("same_day_other_arrivals_included"):
        raise ValueError("Random-lead seed must include other orders arriving on the quoted day")
    if record.get("random_lead_interpretation", "committed-only projection") != "committed-only projection":
        raise ValueError("Adaptive PIL uses committed-only projected arrivals")
    return scenario, theta


def _parameter_bounds(record, theta):
    """Recover the baseline's final search box, including reduced IID fits."""
    search = record.get("search", {})
    rounds = search.get("rounds", [])
    full = search.get("full_parameter_bounds")
    if full is None:
        full = baselines._bounds("forecast_adaptive_pil", Scenario(**record["scenario"]))
    bounds = np.asarray(full, dtype=float).copy()
    if bounds.shape != (5, 2):
        raise ValueError("Invalid full Adaptive PIL parameter bounds")
    if rounds:
        last = np.asarray(rounds[-1]["bounds"], dtype=float)
        if last.shape == (5, 2):
            bounds = last.copy()
        else:
            indices = search.get("active_parameter_indices", [])
            if last.shape != (len(indices), 2):
                raise ValueError("Invalid reduced Adaptive PIL search bounds")
            bounds[np.asarray(indices, dtype=int)] = last
    if not np.isfinite(bounds).all() or np.any(bounds[:, 0] >= bounds[:, 1]):
        raise ValueError("Adaptive PIL parameter bounds must be finite and nondegenerate")
    # Nested-family anchors or later numerical refinement may lie outside the
    # last numerical search box. Preserve the actual frozen initial action.
    bounds[:, 0] = np.minimum(bounds[:, 0], theta)
    bounds[:, 1] = np.maximum(bounds[:, 1], theta)
    return bounds


def seed_code(record):
    """Return the complete editable decision rule at exactly the frozen theta."""
    scenario, theta = _validate_record(record)
    bounds = _parameter_bounds(record, theta)
    lines = ["def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):"]
    for name, value, (low, high) in zip(PARAMETER_NAMES, theta, bounds):
        config = {"initial": float(value), "min": float(low), "max": float(high), "type": "float"}
        lines.append(f"    {name} = {float(value)!r}  # OPT_PARAM: {json.dumps(config)}")
    lines += [
        f"    mean_demand = {float(scenario.mean_demand)!r}",
        "    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)",
        "    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)",
        "    target = max(0.0, mean_demand * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand))",
        "    cap = max(0.0, mean_demand * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))",
        "    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))",
        "    return order_amount",
    ]
    return "\n".join(lines) + "\n"


def seed_helpers_description(record):
    """Public information about injected forecasts; no parameter-count limit."""
    scenario, _ = _validate_record(record)
    forecast = record["forecast"]
    return (
        "Two deterministic numerical helpers are available as ordinary function calls. "
        "conditional_arrival_mean(last_demand, quoted_lead_time) returns the conditional mean "
        "of demand in the period when the current order arrives, D_(t+L), conditional on "
        "the observed D_(t-1). conditional_projected_inventory(on_hand_inventory, pipeline_orders, "
        "last_demand, quoted_lead_time) returns expected on-hand inventory immediately before "
        "the current order is added at t+L. It applies the lost-sales positive-part recursion "
        "separately to each joint conditional demand path through periods t,...,t+L-1, then "
        "includes all OLD orders due at t+L. It assumes no intervening new orders; for random "
        "lead times this is the same committed-only approximation as the frozen Adaptive PIL. "
        f"It uses the original fixed scrambled Sobol bank of {int(forecast['inner_paths'])} paths, "
        f"seed {int(forecast['seed'])}, latent grid spacing {float(forecast['grid_step'])}. "
        "AR forecasts interpolate on the stored demand-signal grid; IID and regime forecasts "
        "use their original conditional models. These helpers observe only their arguments "
        "and the known demand law, never future realized demand, future quotations, or time. "
        f"Use finite nonnegative inventory/demand inputs, the original pipeline length {scenario.max_lead_time-1}, "
        f"and an integer horizon from 1 through {scenario.max_lead_time}. They do not mutate inputs. "
        "The supplied source shows the entire current decision rule. You may change its numerical "
        "coefficients, bounds, arithmetic, branches and use of the helpers; add or remove tunable "
        "coefficients or replace the order formula. The helpers are numerical primitives, not "
        "an immutable order policy.\n"
    )


def _runtime_make_helper_namespace(config, arrays, compiled=True):
    """Standalone factory copied into an isolated worker by trusted source."""
    process_code = int(config["process_code"])
    mu = float(config["mean_demand"])
    maximum_lead = int(config["max_lead_time"])
    count = int(config["inner_paths"])
    if process_code not in (0, 1, 2) or not math.isfinite(mu) or mu <= 0 or maximum_lead < 1:
        raise ValueError("Invalid trusted forecast configuration")
    # Copy before freezing: a caller retaining the original arrays cannot change
    # a forecast after Numba has captured it. No candidate receives these arrays.
    signal_grid = np.array(arrays["signal_grid"], dtype=np.float64, order="C", copy=True)
    demand_paths = np.array(arrays["demand_paths"], dtype=np.float64, order="C", copy=True)
    means = np.array(arrays["means"], dtype=np.float64, order="C", copy=True)
    continuation_counts = np.array(arrays["continuation_counts"], dtype=np.float64, order="C", copy=True)
    if (signal_grid.ndim != 1 or len(signal_grid) < 1 or count < 2 or count & (count - 1)
            or demand_paths.shape != (len(signal_grid), count, maximum_lead + 1)
            or means.shape != (len(signal_grid), maximum_lead + 1)
            or continuation_counts.shape != (count, maximum_lead + 1)):
        raise ValueError("Invalid trusted forecast array shapes")
    if ((process_code == 0 and len(signal_grid) != 1)
            or (process_code == 2 and len(signal_grid) != 2)
            or (process_code == 1 and len(signal_grid) < 2)):
        raise ValueError("Forecast grid does not match the demand process")
    for array in (signal_grid, demand_paths, means, continuation_counts):
        if not np.isfinite(array).all() or np.any(array < 0):
            raise ValueError("Trusted forecast arrays must be finite and nonnegative")
        array.setflags(write=False)
    if np.any(np.diff(signal_grid) <= 0):
        raise ValueError("Forecast signal grid must increase strictly")

    def conditional_arrival_mean(last_demand, quoted_lead_time):
        if (not math.isfinite(last_demand) or last_demand < 0
                or not math.isfinite(quoted_lead_time)):
            raise ValueError("Invalid conditional forecast inputs")
        quote = int(quoted_lead_time)
        if quote != quoted_lead_time or quote < 1 or quote > maximum_lead:
            raise ValueError("Forecast horizon is outside the stored bank")
        lo, hi, weight = _pil_signal_bracket(last_demand, process_code, signal_grid)
        return means[lo, quote] + weight * (means[hi, quote] - means[lo, quote])

    def conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
        if (not math.isfinite(on_hand_inventory) or on_hand_inventory < 0
                or not math.isfinite(last_demand) or last_demand < 0
                or not math.isfinite(quoted_lead_time)
                or len(pipeline_orders) != maximum_lead - 1):
            raise ValueError("Invalid projected inventory inputs")
        quote = int(quoted_lead_time)
        if quote != quoted_lead_time or quote < 1 or quote > maximum_lead:
            raise ValueError("Projection horizon is outside the stored bank")
        for amount in pipeline_orders:
            if not math.isfinite(amount) or amount < 0:
                raise ValueError("Committed arrivals must be finite and nonnegative")
        lo, hi, weight = _pil_signal_bracket(last_demand, process_code, signal_grid)
        if process_code == 0 and quote == 1:
            projected = on_hand_inventory + mu * math.expm1(-on_hand_inventory / mu)
            if len(pipeline_orders) > 0:
                projected += pipeline_orders[0]
            return projected
        return _pil_residual_from_paths(on_hand_inventory, pipeline_orders, quote, lo, hi, weight,
                                        demand_paths, continuation_counts, 0.0)

    if compiled:
        conditional_arrival_mean = njit(conditional_arrival_mean, cache=False)
        conditional_projected_inventory = njit(conditional_projected_inventory, cache=False)
    return {"conditional_projected_inventory": conditional_projected_inventory,
            "conditional_arrival_mean": conditional_arrival_mean}


def trusted_runtime_source():
    """Self-contained numerical source; exec with np, math, njit in globals.

    The resulting make_helper_namespace(config, arrays, compiled=True) returns
    only the two callable primitives. No repository import is needed by a worker.
    """
    parts = []
    for dispatcher in (baselines._signal_bracket, baselines._residual_from_paths):
        tree = ast.parse(inspect.getsource(dispatcher.py_func))
        tree.body[0].decorator_list = []
        parts.append(ast.unparse(tree))
    parts.append("_pil_signal_bracket = njit(_signal_bracket, cache=False)")
    parts.append("_pil_residual_from_paths = njit(_residual_from_paths, cache=False)")
    factory = ast.parse(inspect.getsource(_runtime_make_helper_namespace))
    factory.body[0].name = "make_helper_namespace"
    parts.append(ast.unparse(factory))
    return "\n\n".join(parts) + "\n"


def build_runtime_payload(record):
    """Build immutable bank arrays and a JSON identity from a frozen record."""
    scenario, _ = _validate_record(record)
    forecast = record["forecast"]
    bank = baselines.forecast_bank(scenario, inner_paths=forecast["inner_paths"],
                                   seed=forecast["seed"], grid_step=forecast["grid_step"])
    arrays = {name: np.array(value, dtype=np.float64, order="C", copy=True)
              for name, value in zip(ARRAY_NAMES, bank[1:])}
    digest = hashlib.sha256()
    for name, array in arrays.items():
        array.setflags(write=False)
        digest.update(name.encode())
        digest.update(str(array.shape).encode())
        digest.update(array.tobytes())
    config = {
        "version": VERSION, "baseline_version": record["version"], "scenario": scenario.to_dict(),
        "process_code": int(bank[0]), "mean_demand": float(scenario.mean_demand),
        "max_lead_time": scenario.max_lead_time, "inner_paths": int(forecast["inner_paths"]),
        "seed": int(forecast["seed"]), "grid_step": float(forecast["grid_step"]),
        "baseline_record_sha256": _json_hash(record), "bank_sha256": digest.hexdigest(),
        "runtime_source_sha256": hashlib.sha256(trusted_runtime_source().encode()).hexdigest(),
        "projection": "committed-only; includes old arrivals on the quoted arrival day",
    }
    return config, arrays


def make_helper_namespace(record, *, compiled=True):
    """Parent-side convenience equivalent to the isolated worker's injection."""
    config, arrays = build_runtime_payload(record)
    namespace = {"np": np, "math": math, "njit": njit}
    exec(compile(trusted_runtime_source(), "trusted_adaptive_pil.py", "exec"), namespace)
    return namespace["make_helper_namespace"](config, arrays, compiled=compiled)


def make_seed_policy(record, *, compiled=True):
    """Reconstruct the editable seed for offline numerical comparisons."""
    namespace = make_helper_namespace(record, compiled=compiled)
    exec(compile(seed_code(record), "adaptive_pil_seed_policy.py", "exec"), namespace)
    policy = namespace["compute_order_amount"]
    return njit(policy, cache=False) if compiled else policy
