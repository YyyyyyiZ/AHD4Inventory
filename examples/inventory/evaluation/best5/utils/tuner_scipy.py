"""
utils/tuner_scipy.py  (Pro version)

SciPy-based tuning of OPT_PARAM parameters on training instances.

Improvements over the basic version
- Avoid repeated exec() per instance by compiling once per candidate code
- Safe objective: exceptions -> large penalty cost (prevents optimizer crash)
- Adaptive bounds for cross-distribution generalization
- Iterative bound expansion when the optimizer lands on bounds
- Screening subset (fast) + full confirmation (train) optimization
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize

from .datasets import demand_stats
from .inventory_sim import evaluate_policy_avg
from .opt_params import (
    parse_opt_params,
    adapt_bounds_for_dataset,
    vectorize,
    unvectorize,
    replace_params_in_code,
    bound_hits,
    expand_bounds,
)


@dataclass
class TuneResult:
    tuned_code: str
    tuned_params: Dict[str, Any]
    train_avg: float
    status: str


def tune_policy_on_train(
    code: str,
    train_instances: List[Dict[str, Any]],
    *,
    seed: int = 0,
    screen_n: int = 150,
    maxiter_screen: int = 25,
    maxiter_full: int = 35,
    max_expand: int = 3,
    hit_frac: float = 0.01,
    penalty_cost: float = 1e18,
) -> TuneResult:
    """
    Tune OPT_PARAM variables to minimize average total cost on train_instances.

    Returns tuned_code (code string with parameters replaced) and tuned_params dict.
    """
    params0 = parse_opt_params(code)
    if not params0:
        # no tunable parameters
        avg = evaluate_policy_avg(code, train_instances, use_cache=False)
        return TuneResult(tuned_code=code, tuned_params={}, train_avg=avg, status="no_opt_param")

    stats = demand_stats(train_instances)
    cur_params = adapt_bounds_for_dataset(
        params0,
        mean_d=stats["mean"],
        std_d=stats["std"],
        p95_d=stats["p95"],
        max_d=stats["max"],
        lead_time=int(stats["L"]),
    )

    rng = np.random.default_rng(seed)
    N = len(train_instances)
    if N > screen_n:
        idx = rng.choice(N, size=screen_n, replace=False)
        train_screen = [train_instances[i] for i in idx]
    else:
        train_screen = train_instances

    def objective(instances, names, params):
        def f(x):
            try:
                pv = unvectorize(list(x), names, params)
                code2 = replace_params_in_code(code, pv)
                return float(evaluate_policy_avg(code2, instances, use_cache=False))
            except Exception:
                return float(penalty_cost)
        return f

    best_x = None
    best_val = float("inf")

    for _round in range(max_expand + 1):
        names, x0, bnds = vectorize(cur_params)
        x0_arr = np.array(x0, dtype=float)

        # Stage 1: screening optimization
        res1 = minimize(
            objective(train_screen, names, cur_params),
            x0=x0_arr,
            method="L-BFGS-B",
            bounds=bnds,
            options={"maxiter": maxiter_screen},
        )

        # Stage 2: full training confirmation
        res2 = minimize(
            objective(train_instances, names, cur_params),
            x0=np.array(res1.x, dtype=float),
            method="L-BFGS-B",
            bounds=bnds,
            options={"maxiter": maxiter_full},
        )

        x = list(np.array(res2.x, dtype=float))
        v = float(res2.fun)

        if v < best_val:
            best_val = v
            best_x = x

        hits = bound_hits(best_x, bnds, frac=hit_frac)
        if not hits:
            break

        # Expand bounds and try again
        cur_params = expand_bounds(
            cur_params,
            names,
            hits,
            mean_d=stats["mean"],
            std_d=stats["std"],
            p95_d=stats["p95"],
            max_d=stats["max"],
            lead_time=int(stats["L"]),
        )

    if best_x is None:
        avg = evaluate_policy_avg(code, train_instances, use_cache=False)
        return TuneResult(tuned_code=code, tuned_params={}, train_avg=avg, status="failed")

    tuned_params = unvectorize(best_x, sorted(cur_params.keys()), cur_params)
    tuned_code = replace_params_in_code(code, tuned_params)
    return TuneResult(tuned_code=tuned_code, tuned_params=tuned_params, train_avg=best_val, status="ok")
