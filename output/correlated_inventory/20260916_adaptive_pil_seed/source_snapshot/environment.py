"""Common scalar reference / Numba-compatible inventory transition kernel.

Each period is arrival -> quotation and order -> demand -> cost. Orders may
overtake. The policy sees only on-hand inventory, amounts due in future periods
1..M-1, previous realized demand, and the current quoted lead time. Demand is
fully observed after the decision even when sales were lost. There are no free
preparation periods, terminal liquidation, or hidden policy counters.

This module is an environment, not an OS security boundary for untrusted code.
"""

from __future__ import annotations

import math
from numbers import Integral, Real

import numpy as np

from .data import Scenario, validate_tapes


TRACE_COLUMNS = ("arrivals", "on_hand_before_order", "last_demand", "quoted_lead_time",
                 "order", "demand", "sales", "lost_units", "ending_inventory", "scored")


class InvalidPolicyError(ValueError):
    pass


def simulate_kernel(policy, demands, lead_times, initial_last_demand, max_lead_time,
                    holding_rate, lost_rate, horizon, burnin, return_trace=False):
    """Pure numerical kernel suitable for ``numba.njit`` and compiled policies.

    Inputs must already be validated. ``policy`` is called positionally with
    (float, independent float64[M-1] array, float, int). Returns holding costs,
    lost-sales costs, demand units, sales units, lost units, and optional trace.
    All five metric arrays have shape [N]. Trace has shape [N,B+H,10+M-1], or
    [0,0,0] when disabled. The final columns are the policy's input pipeline.
    """
    n_paths = demands.shape[0]
    periods = burnin + horizon
    holds = np.zeros(n_paths, dtype=np.float64)
    lost_costs = np.zeros(n_paths, dtype=np.float64)
    demand_totals = np.zeros(n_paths, dtype=np.float64)
    sales_totals = np.zeros(n_paths, dtype=np.float64)
    lost_totals = np.zeros(n_paths, dtype=np.float64)
    if return_trace:
        trace = np.empty((n_paths, periods, 10 + max_lead_time - 1), dtype=np.float64)
    else:
        trace = np.empty((0, 0, 0), dtype=np.float64)
    for path in range(n_paths):
        inventory = 0.0
        calendar = np.zeros(max_lead_time, dtype=np.float64)
        last_demand = initial_last_demand[path]
        for t in range(periods):
            slot = t % max_lead_time
            arrivals = calendar[slot]
            inventory += arrivals
            calendar[slot] = 0.0
            pipeline = np.empty(max_lead_time - 1, dtype=np.float64)
            for k in range(1, max_lead_time):
                pipeline[k - 1] = calendar[(t + k) % max_lead_time]
                if return_trace:
                    trace[path, t, 10 + k - 1] = pipeline[k - 1]
            quote = int(lead_times[path, t])
            if return_trace:
                trace[path, t, 0] = arrivals
                trace[path, t, 1] = inventory
                trace[path, t, 2] = last_demand
                trace[path, t, 3] = quote
            if not math.isfinite(inventory):
                raise ValueError("Inventory overflow")
            order = policy(inventory, pipeline, last_demand, quote)
            if isinstance(order, bool) or not math.isfinite(order) or order < 0.0:
                raise ValueError("Policy order must be finite and nonnegative")
            calendar[(t + quote) % max_lead_time] += order
            if not math.isfinite(calendar[(t + quote) % max_lead_time]):
                raise ValueError("Pipeline overflow")
            demand = demands[path, t]
            sales = min(inventory, demand)
            lost = demand - sales
            inventory -= sales
            if t >= burnin:
                holds[path] += holding_rate * inventory
                lost_costs[path] += lost_rate * lost
                demand_totals[path] += demand
                sales_totals[path] += sales
                lost_totals[path] += lost
            if return_trace:
                trace[path, t, 4] = order
                trace[path, t, 5] = demand
                trace[path, t, 6] = sales
                trace[path, t, 7] = lost
                trace[path, t, 8] = inventory
                trace[path, t, 9] = 1.0 if t >= burnin else 0.0
            last_demand = demand
        if not math.isfinite(holds[path]) or not math.isfinite(lost_costs[path]):
            raise ValueError("Cost overflow")
    return holds, lost_costs, demand_totals, sales_totals, lost_totals, trace


def _validate_window(tapes, scenario, horizon, burnin):
    if isinstance(horizon, (bool, np.bool_)) or not isinstance(horizon, Integral) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if isinstance(burnin, (bool, np.bool_)) or not isinstance(burnin, Integral) or burnin < 0:
        raise ValueError("burnin must be a nonnegative integer")
    normalized = validate_tapes(tapes, scenario)
    if burnin + horizon > normalized["demands"].shape[1]:
        raise ValueError("Tape is shorter than burnin + horizon")
    return normalized


def summarize_kernel(result, *, horizon, burnin, scenario, return_trace=False):
    holds, shortage, demand, sales, lost, trace = result
    total = holds + shortage
    fill = np.divide(sales, demand, out=np.ones_like(sales), where=demand > 0)
    answer = {"total_cost": total, "holding_cost": holds, "lost_sales_cost": shortage,
              "demand_units": demand, "sales_units": sales, "lost_units": lost,
              "service_level": fill, "cost_per_period": total / horizon,
              "mean_cost": float(total.mean()), "mean_cost_per_period": float(total.mean() / horizon),
              "horizon": int(horizon), "burnin": int(burnin), "n_paths": len(total),
              "periods_simulated": int(horizon + burnin), "periods_scored": int(horizon),
              "mode": "cold_start" if burnin == 0 else "steady", "scenario_id": scenario.scenario_id}
    if return_trace:
        answer["trace"] = trace
        answer["trace_columns"] = TRACE_COLUMNS + tuple(f"pipeline_due_{k}" for k in range(1, scenario.max_lead_time))
        answer["order_matrix"] = trace[:, burnin:, 4]
        answer["cost_matrix"] = np.stack((scenario.holding_cost * trace[:, burnin:, 8],
                                          scenario.lost_sales_cost * trace[:, burnin:, 7]), axis=2)
    for value in answer.values():
        if isinstance(value, np.ndarray):
            value.setflags(write=False)
    return answer


def simulate_callable(policy, tapes, scenario: Scenario, horizon: int, burnin: int,
                      return_trace: bool = False) -> dict:
    """Validated scalar reference using the same kernel as accelerated scoring."""
    if not callable(policy):
        raise TypeError("policy must be callable")
    normalized = _validate_window(tapes, scenario, horizon, burnin)

    def adapter(inventory, pipeline, last_demand, quote):
        try:
            action = policy(on_hand_inventory=float(inventory), pipeline_orders=pipeline,
                            last_demand=float(last_demand), quoted_lead_time=int(quote))
        except Exception as exc:
            raise InvalidPolicyError(f"Policy raised {type(exc).__name__}: {exc}") from exc
        if isinstance(action, (bool, np.bool_)) or not isinstance(action, Real):
            raise InvalidPolicyError("Policy order must be a real scalar, excluding bool")
        if not math.isfinite(action) or action < 0:
            raise InvalidPolicyError("Policy order must be finite and nonnegative")
        return float(action)

    result = simulate_kernel(adapter, normalized["demands"], normalized["lead_times"],
                             normalized["initial_last_demand"], scenario.max_lead_time,
                             scenario.holding_cost, scenario.lost_sales_cost, int(horizon), int(burnin), bool(return_trace))
    return summarize_kernel(result, horizon=horizon, burnin=burnin, scenario=scenario, return_trace=return_trace)


_compiled_kernel = None


def simulate_compiled(policy, tapes, scenario: Scenario, horizon: int, burnin: int,
                      return_trace: bool = False) -> dict:
    """Validated fast path; ``policy`` must be a Numba-compiled scalar callable."""
    global _compiled_kernel
    from numba import njit
    normalized = _validate_window(tapes, scenario, horizon, burnin)
    if _compiled_kernel is None:
        _compiled_kernel = njit(simulate_kernel, cache=True)
    result = _compiled_kernel(policy, normalized["demands"], normalized["lead_times"],
                              normalized["initial_last_demand"], scenario.max_lead_time,
                              scenario.holding_cost, scenario.lost_sales_cost, int(horizon), int(burnin), bool(return_trace))
    return summarize_kernel(result, horizon=horizon, burnin=burnin, scenario=scenario, return_trace=return_trace)
