"""
utils/inventory_sim.py  (Pro version)

Inventory simulation and evaluation utilities.

Hard constraints (per project requirements)
- order_before_sell sequence
- demand padding: prepend L zeros to selling-horizon demand
- planning phase of length L: NO demand and NO costs (holding/lost) in periods 0..L-1

Event sequence per period (order_before_sell)
1) Receive incoming shipment (pipeline FIFO)
2) Compute order quantity based on on_hand + outstanding pipeline (excluding new order)
3) Realize demand and update on_hand (sell / lost)
4) Place the order into pipeline (arrives after L periods)
5) Accumulate costs (only in selling phase t >= L)

We keep outputs compatible with run.py style:
- avg, lower, upper, trajectory (list of total costs per instance)
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from .policy_exec import compile_policy, call_policy


def _pad_demand(demand_sell: List[float], L: int) -> List[float]:
    return [0.0] * L + [float(x) for x in demand_sell]


def simulate_instance_order_before_sell_fn(fn, instance: Dict[str, Any]) -> float:
    """
    Simulate ONE instance given a compiled compute_order_amount fn.
    Returns total cost (sum over selling horizon costs only).
    """
    L = int(instance["lead_time"])
    h = float(instance["holding_cost"])
    p = float(instance["lost_sales_cost"])

    demand_raw = instance.get("demand", [])
    T_sell = int(instance.get("num_periods", len(demand_raw)))
    T_sell = min(T_sell, len(demand_raw))

    demand = _pad_demand(demand_raw[:T_sell], L)
    T_total = L + T_sell

    inv = float(instance["initial_inventory"])
    pipeline = [0.0] * L  # FIFO, oldest first

    total_cost = 0.0

    for t in range(T_total):
        # 1) Receive incoming shipment
        if L > 0:
            incoming = pipeline.pop(0)
            inv += incoming

        # 2) Compute order amount BEFORE demand (policy sees outstanding pipeline, excluding incoming and new order)
        order = call_policy(fn, on_hand=inv, pipeline=pipeline)

        # 3) Demand
        d = float(demand[t])
        sales = min(inv, d)
        lost = max(0.0, d - sales)
        inv -= sales

        # 4) Place order (arrives after L periods)
        if L > 0:
            pipeline.append(order)
        else:
            # L==0: order arrives immediately; in order-before-sell semantics it should be available before demand.
            # However, L==0 is not expected in your experiments. We keep a conservative implementation:
            # treat it as immediate arrival after ordering; demand already realized above, so this does not help
            # current period. If you need L==0, adjust accordingly.
            inv += order

        # 5) Cost only in selling phase (t >= L)
        if t >= L:
            total_cost += h * inv + p * lost

    return total_cost


def evaluate_policy(
    code: str,
    instances: List[Dict[str, Any]],
    *,
    seed: int = 0,
    n_bootstrap: int = 300,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Full evaluation: returns avg cost, bootstrap CI, and trajectory list.
    """
    compiled = compile_policy(code, use_cache=use_cache)
    costs = [simulate_instance_order_before_sell_fn(compiled.fn, inst) for inst in instances]
    avg = float(np.mean(costs)) if costs else float("inf")

    lower, upper = (float("nan"), float("nan"))
    if costs and n_bootstrap and n_bootstrap > 0:
        lower, upper = bootstrap_ci(costs, n_bootstrap=n_bootstrap, ci=95, seed=seed)

    return {"avg": avg, "lower": lower, "upper": upper, "trajectory": costs}


def evaluate_policy_avg(
    code: str,
    instances: List[Dict[str, Any]],
    *,
    use_cache: bool = False,
) -> float:
    """
    Fast average evaluation (no CI, no trajectory list kept).
    Intended for optimization inner loops.
    """
    compiled = compile_policy(code, use_cache=use_cache)
    s = 0.0
    n = 0
    for inst in instances:
        s += float(simulate_instance_order_before_sell_fn(compiled.fn, inst))
        n += 1
    return s / n if n > 0 else float("inf")


def bootstrap_ci(data: List[float], *, n_bootstrap: int = 1000, ci: int = 95, seed: int = 0) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    arr = np.asarray(data, dtype=float)
    n = len(arr)
    means = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        means.append(float(arr[idx].mean()))
    lower = float(np.percentile(means, (100 - ci) / 2))
    upper = float(np.percentile(means, 100 - (100 - ci) / 2))
    return lower, upper
