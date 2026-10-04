"""Classical inventory baselines fitted to training paths only.

The deterministic grid searches below optimize the same finite sales horizon as
the main experiment. They do not open data files or inspect test scores. Returned
fit records are JSON serializable; use ``make_policy`` to reconstruct a policy.
"""

from __future__ import annotations

from itertools import product
import hashlib
import math
from typing import Callable

import numpy as np

from .environment import Scenario, SimulationResult


NAMES = ("base_stock", "constant_order", "capped_base_stock")
SEARCH_VERSION = "training-grid-refine-v1"


def _demands(values, scenario: Scenario) -> np.ndarray:
    raw = np.asarray(values)
    if np.iscomplexobj(raw):
        raise ValueError("Demand must be real")
    array = np.asarray(raw, dtype=float)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] != scenario.horizon:
        raise ValueError("Expected nonempty (n_paths, scenario.horizon) sales demand")
    if not np.isfinite(array).all() or (array < 0).any():
        raise ValueError("Demand must be finite and nonnegative")
    return array


def _parameters(name: str, params: dict) -> dict[str, float]:
    keys = {"base_stock": ("S",), "constant_order": ("q",),
            "capped_base_stock": ("S", "cap")}
    if name not in keys:
        raise ValueError(f"Unknown baseline {name!r}")
    if set(params) != set(keys[name]):
        raise ValueError(f"{name} requires parameters {keys[name]}")
    result = {key: float(params[key]) for key in keys[name]}
    if any(not math.isfinite(value) or value < 0 for value in result.values()):
        raise ValueError("Baseline parameters must be finite and nonnegative")
    return result


def make_policy(name: str, params: dict) -> Callable:
    """Create a stationary policy with the environment's named interface."""
    values = _parameters(name, params)

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        if name == "constant_order":
            return values["q"]
        gap = max(0.0, values["S"] - on_hand_inventory - sum(pipeline_orders))
        return min(gap, values["cap"]) if name == "capped_base_stock" else gap

    return compute_order_amount


def _simulate_candidates(name, candidates, demands, scenario, *, integer_orders=False):
    """Independent simulator, vectorized over both parameter sets and paths."""
    params = [_parameters(name, item) for item in candidates]
    n_candidates, n_paths = len(params), len(demands)
    lead = scenario.lead_time
    inventory = np.zeros((n_candidates, n_paths), dtype=float)
    pipeline = np.zeros((lead, n_candidates, n_paths), dtype=float)
    holding = np.zeros_like(inventory)
    lost_units = np.zeros_like(inventory)
    target = np.array([item.get("S", 0.0) for item in params])[:, None]
    cap = np.array([item.get("cap", item.get("q", 0.0)) for item in params])[:, None]
    for t in range(lead + demands.shape[1]):
        position = t % lead
        inventory += pipeline[position]
        pipeline[position] = 0.0
        if name == "constant_order":
            order = np.broadcast_to(cap, inventory.shape)
        else:
            order = np.maximum(0.0, target - inventory - pipeline.sum(axis=0))
            if name == "capped_base_stock":
                order = np.minimum(order, cap)
        if integer_orders:
            order = np.rint(order)
        pipeline[position] = order
        if t >= lead:
            demand = demands[:, t - lead][None, :]
            lost_units += np.maximum(0.0, demand - inventory)
            inventory = np.maximum(0.0, inventory - demand)
            holding += scenario.holding_cost * inventory
    return holding, scenario.lost_sales_cost * lost_units, lost_units


def evaluate_classical(name: str, params: dict, demands, scenario: Scenario,
                       *, integer_orders: bool = False) -> SimulationResult:
    """Score fixed parameters; independently auditable against simulate_policy."""
    array = _demands(demands, scenario)
    holding, shortage, lost = _simulate_candidates(
        name, [params], array, scenario, integer_orders=integer_orders)
    holding, shortage, lost = holding[0], shortage[0], lost[0]
    totals = array.sum(axis=1)
    sales = totals - lost
    fill = np.divide(sales, totals, out=np.ones_like(sales), where=totals > 0)
    return SimulationResult(
        total_cost=holding + shortage, holding_cost=holding,
        lost_sales_cost=shortage, demand_units=totals, sales_units=sales,
        lost_units=lost, service_level=fill, policy_seconds=np.zeros(len(array)),
        periods_scored=scenario.horizon,
        periods_simulated=scenario.horizon + scenario.lead_time,
        mode="finite", integer_orders=integer_orders,
    )


def _search(name, demands, scenario, initial_upper, *, anchors=()):
    """Global grid followed by local grids around three distinct best points.

    Upper bounds double if a selected minimizer lies at an artificial upper
    edge. At most four expansions are allowed and unresolved edges are reported.
    Zero is a physical action boundary and is not expanded. This is a finite
    deterministic parameter search, not a claim of exact policy optimization.
    """
    keys = ("S", "cap") if name == "capped_base_stock" else (
        "S",) if name == "base_stock" else ("q",)
    upper = np.array(initial_upper, dtype=float)
    cache: dict[tuple[float, ...], float] = {}
    rounds = []

    def score(points):
        pending = sorted({tuple(float(x) for x in point) for point in points} - cache.keys())
        for start in range(0, len(pending), 128):
            batch = pending[start:start + 128]
            candidates = [dict(zip(keys, point)) for point in batch]
            hold, shortage, _ = _simulate_candidates(name, candidates, demands, scenario)
            costs = (hold + shortage).mean(axis=1)
            for point, cost in zip(batch, costs):
                cache[point] = float(cost)

    for expansion in range(5):
        size = 25 if len(keys) == 2 else 97
        grid = [np.linspace(0.0, bound, size) for bound in upper]
        score(product(*grid))
        score(point for point in anchors if all(0 <= x <= b for x, b in zip(point, upper)))
        step = upper / (size - 1)
        for _ in range(5):
            best_points = sorted(cache, key=lambda point: (cache[point], point))[:3]
            candidates = []
            for center in best_points:
                axes = [np.linspace(max(0.0, x - delta), min(bound, x + delta), 9)
                        for x, delta, bound in zip(center, step, upper)]
                candidates.extend(product(*axes))
            score(candidates)
            step /= 4.0
        best = min(cache, key=lambda point: (cache[point], point))
        edge = [bool(x >= bound - max(1e-9, bound * 1e-8))
                for x, bound in zip(best, upper)]
        rounds.append({"upper": dict(zip(keys, map(float, upper))),
                       "best_params": dict(zip(keys, best)),
                       "train_mean_cost": cache[best], "upper_edge": dict(zip(keys, edge))})
        if not any(edge):
            break
        if expansion < 4:
            upper *= np.where(edge, 2.0, 1.0)
    return {
        "name": name, "params": dict(zip(keys, best)),
        "train_mean_cost": cache[best],
        "search": {"version": SEARCH_VERSION, "parameter_sets_scored": len(cache),
                   "initial_upper": dict(zip(keys, map(float, initial_upper))),
                   "rounds": rounds, "unresolved_upper_edge": any(edge),
                   "continuous_actions": True, "integer_orders": False},
    }


def fit_baselines(train_demands, scenario: Scenario, *, n_train: int = 50) -> dict:
    """Fit all three families to the first n_train supplied training paths.

    Normal experiments use exactly 50 paths. A smaller explicit n_train supports
    synthetic correctness checks. The caller supplies training data explicitly;
    this function never reads test files. No stochastic optimizer is involved.
    """
    array = _demands(train_demands, scenario)
    if isinstance(n_train, bool) or not isinstance(n_train, int) or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if len(array) < n_train:
        raise ValueError(f"Need {n_train} training paths, received {len(array)}")
    array = array[:n_train]
    mean, sd = float(array.mean()), float(array.std())
    # Depend solely on training samples. Bound expansions diagnose extremes.
    upper_q = max(1.0, mean + 6.0 * sd, float(np.quantile(array, 0.995)))
    upper_s = max(1.0, mean * (scenario.lead_time + 1)
                  + 6.0 * sd * math.sqrt(scenario.lead_time + 1), upper_q)
    fitted = {}
    fitted["base_stock"] = _search("base_stock", array, scenario, [upper_s])
    fitted["constant_order"] = _search("constant_order", array, scenario, [upper_q])
    # Include exact embeddings of both fitted families as final candidates.
    # S >= (L+T)*q realizes constant q even on a zero-demand finite trajectory.
    # These anchors need not enlarge the economically useful global search grid.
    bs_s = fitted["base_stock"]["params"]["S"]
    q = fitted["constant_order"]["params"]["q"]
    capped_upper = [upper_s, upper_q]
    anchors = [(bs_s, bs_s), ((scenario.lead_time + scenario.horizon) * q, q)]
    fitted["capped_base_stock"] = _search(
        "capped_base_stock", array, scenario, capped_upper, anchors=anchors)
    cap_result = fitted["capped_base_stock"]
    anchor_params = [{"S": float(S), "cap": float(cap)} for S, cap in anchors]
    holds, losses, _ = _simulate_candidates("capped_base_stock", anchor_params, array, scenario)
    anchor_costs = (holds + losses).mean(axis=1)
    cap_result["search"]["embedded_family_candidates"] = [
        {"family": family, "params": params, "train_mean_cost": float(cost)}
        for family, params, cost in zip(("base_stock", "constant_order"), anchor_params, anchor_costs)]
    for family, params, cost in zip(("base_stock", "constant_order"), anchor_params, anchor_costs):
        if float(cost) < cap_result["train_mean_cost"]:
            cap_result.update(params=params, train_mean_cost=float(cost))
            cap_result["search"]["selected_embedded_family"] = family
    for result in fitted.values():
        result.update(scenario_id=scenario.scenario_id, n_train=n_train,
                      training_selection="first_n_paths", horizon=scenario.horizon,
                      planning_periods=scenario.lead_time,
                      training_demands_sha256=hashlib.sha256(
                          np.ascontiguousarray(array, dtype="<f8").tobytes()).hexdigest())
    return fitted
