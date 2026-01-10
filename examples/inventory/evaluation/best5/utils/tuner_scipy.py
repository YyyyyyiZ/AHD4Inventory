"""
utils/tuner_scipy.py  (derivative-free)

Despite the filename, v3 does NOT rely on SciPy for tuning. The key issue observed in results is that
gradient-based L-BFGS-B often returns the original OPT_PARAM initial values across many datasets
(flat/non-smooth objective, integer thresholds, min/max caps, etc.). This leads to very poor
generalization performance.

v3 fixes this by:
1) Recalibrating parameter (min,max,initial) using the new training dataset demand statistics.
2) Using a derivative-free, bound-flexible search:
   - successive halving random search (cheap -> expensive)
   - coordinate pattern refinement around the best candidates
3) Optional bound expansion if the best candidate repeatedly hits a boundary.

This approach works even when the "true" useful range is unknown a priori.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np

from .datasets import demand_stats
from .inventory_sim import simulate_instance_order_before_sell_fn
from .opt_params import (
    parse_opt_params,
    filter_unused_opt_params,
    recalibrate_params_for_dataset,
    replace_params_in_code,
    OptParam,
)
from .policy_exec import compile_parametric_policy


@dataclass
class TuneResult:
    tuned_code: str
    tuned_params: Dict[str, Any]
    train_avg: float
    status: str


def _avg_cost_on_instances(fn, instances: List[Dict[str, Any]]) -> float:
    if not instances:
        return float("inf")
    s = 0.0
    for inst in instances:
        s += float(simulate_instance_order_before_sell_fn(fn, inst))
    return s / float(len(instances))


def _clip_cast(v: float, p: OptParam) -> Any:
    lo, hi = float(p.min), float(p.max)
    vv = float(v)
    vv = min(max(vv, lo), hi)
    if p.type == "int":
        return int(round(vv))
    return float(vv)


def _is_prob_param(p: OptParam) -> bool:
    return p.min >= 0.0 and p.max <= 1.0


def _sample_param(rng: np.random.Generator, p: OptParam) -> float:
    lo, hi = float(p.min), float(p.max)
    if hi <= lo:
        return float(p.initial)

    if _is_prob_param(p):
        # sample around initial with mild concentration
        mu = float(p.initial)
        mu = min(max(mu, 0.0), 1.0)
        # Convert mean+concentration to Beta(a,b)
        k = 8.0  # concentration
        a = max(mu * k, 1e-3)
        b = max((1.0 - mu) * k, 1e-3)
        x = float(rng.beta(a, b))
        return min(max(x, lo), hi)

    # Positive-ish: use mixture of log-uniform (explore) and log-normal around initial (exploit)
    if lo >= 0.0 and hi > 0.0:
        lo_eps = max(lo, 1e-6)
        if rng.random() < 0.5:
            # log-uniform over [lo_eps, hi]
            u = rng.random()
            x = lo_eps * (hi / lo_eps) ** u
            return float(x)
        else:
            # log-normal around initial
            init = max(float(p.initial), lo_eps)
            sigma = 0.8
            x = init * float(np.exp(rng.normal(0.0, sigma)))
            return float(min(max(x, lo), hi))

    # General fallback: uniform
    return float(rng.uniform(lo, hi))


def _make_candidate(rng: np.random.Generator, params: Dict[str, OptParam]) -> Dict[str, Any]:
    cand: Dict[str, Any] = {}
    for name, p in params.items():
        x = _sample_param(rng, p)
        cand[name] = _clip_cast(x, p)
    return cand


def _near_bounds(values: Dict[str, Any], params: Dict[str, OptParam], frac: float = 0.05) -> List[Tuple[str, str]]:
    hits = []
    for name, p in params.items():
        lo, hi = float(p.min), float(p.max)
        if hi <= lo:
            continue
        x = float(values[name])
        if (x - lo) / (hi - lo) <= frac:
            hits.append((name, "lower"))
        if (hi - x) / (hi - lo) <= frac:
            hits.append((name, "upper"))
    return hits


def _expand_params_bounds(
    params: Dict[str, OptParam],
    values: Dict[str, Any],
    stats: Dict[str, float],
    hits: List[Tuple[str, str]],
) -> Dict[str, OptParam]:
    """
    Expand bounds for params that land near a boundary.
    Expansion amount is tied to demand scale (mean/p95/max) and lead time.
    """
    mean_d = float(stats["mean"])
    std_d = float(stats["std"])
    p95_d = float(stats["p95"])
    max_d = float(stats["max"])
    L = float(stats["L"])
    scale_add = max(p95_d * (L + 1.0), (mean_d + 2.0 * std_d) * (L + 1.0), 50.0)

    out: Dict[str, OptParam] = dict(params)
    for name, side in hits:
        p = out[name]
        lo, hi = float(p.min), float(p.max)
        init = float(values[name])
        if side == "upper":
            new_max = max(hi * 2.0 if hi > 0 else hi + scale_add, hi + 0.5 * scale_add)
            out[name] = OptParam(name=name, initial=init, min=lo, max=new_max, type=p.type)
        else:
            new_min = 0.0 if lo >= 0.0 else lo * 2.0
            out[name] = OptParam(name=name, initial=init, min=new_min, max=hi, type=p.type)
    return out


def _pattern_refine(
    rng: np.random.Generator,
    policy_fn,
    policy_params_dict: Dict[str, Any],
    params: Dict[str, OptParam],
    start: Dict[str, Any],
    instances: List[Dict[str, Any]],
    *,
    n_rounds: int = 3,
) -> Tuple[Dict[str, Any], float]:
    """
    Simple coordinate pattern search refinement.

    For each round, step sizes shrink, and for each parameter we try +/- moves (or multiplicative
    moves for nonnegative ranges). Accept improving moves greedily.
    """
    best = dict(start)
    # set params and evaluate
    policy_params_dict.update(best)
    best_cost = _avg_cost_on_instances(policy_fn, instances)

    names = list(params.keys())
    # Shuffle order each refinement run to reduce bias
    rng.shuffle(names)

    for r in range(n_rounds):
        # Multiplicative factors shrink towards 1
        mult = 2.0 ** (1.0 / (r + 1.0))
        for name in names:
            p = params[name]
            lo, hi = float(p.min), float(p.max)
            x0 = float(best[name])

            candidates = []
            if _is_prob_param(p):
                # additive step in prob space
                step = 0.2 / (r + 1.0)
                candidates = [x0 - step, x0 + step]
            elif lo >= 0.0:
                # multiplicative moves
                candidates = [x0 / mult, x0 * mult]
            else:
                # additive moves based on span
                span = hi - lo
                step = 0.25 * span / (r + 1.0)
                candidates = [x0 - step, x0 + step]

            for x in candidates:
                v = _clip_cast(x, p)
                if v == best[name]:
                    continue
                trial = dict(best)
                trial[name] = v
                policy_params_dict.update(trial)
                c = _avg_cost_on_instances(policy_fn, instances)
                if c < best_cost:
                    best = trial
                    best_cost = c

    return best, best_cost


def tune_policy_on_train(
    code: str,
    train_instances: List[Dict[str, Any]],
    *,
    seed: int = 0,
    screen_n: int = 150,
    max_expand: int = 2,
) -> TuneResult:
    """
    Main tuning entry point (same signature as previous versions).
    """
    params0 = parse_opt_params(code)
    params0 = filter_unused_opt_params(code, params0)

    if not params0:
        # No tunable params (or all unused)
        return TuneResult(tuned_code=code, tuned_params={}, train_avg=_avg_cost_on_instances(compile_parametric_policy(code, [], {}).fn, train_instances), status="no_opt_param")

    stats = demand_stats(train_instances)
    params = recalibrate_params_for_dataset(
        params0,
        mean_d=stats["mean"],
        std_d=stats["std"],
        p95_d=stats["p95"],
        max_d=stats["max"],
        lead_time=int(stats["L"]),
    )

    rng = np.random.default_rng(seed)

    # Successive-halving subsets
    N = len(train_instances)
    if N <= 0:
        return TuneResult(tuned_code=code, tuned_params={}, train_avg=float("inf"), status="empty_train")

    n_small = min(30, N)
    n_mid = min(max(40, screen_n), N)

    idx_small = rng.choice(N, size=n_small, replace=False) if N > n_small else np.arange(N)
    idx_mid = rng.choice(N, size=n_mid, replace=False) if N > n_mid else np.arange(N)

    inst_small = [train_instances[int(i)] for i in idx_small]
    inst_mid = [train_instances[int(i)] for i in idx_mid]

    # Prepare parametric policy (single exec)
    names = sorted(params.keys())
    init_params = {n: _clip_cast(params[n].initial, params[n]) for n in names}
    param_policy = compile_parametric_policy(code, names, init_params)

    def eval_values(values: Dict[str, Any], instances: List[Dict[str, Any]]) -> float:
        # Update in-place dict used by policy
        param_policy.params.update(values)
        return _avg_cost_on_instances(param_policy.fn, instances)

    # Initial candidate
    best_values = dict(init_params)
    best_cost_small = eval_values(best_values, inst_small)

    # Determine number of random samples based on dimension
    dim = len(names)
    n_samples = max(50, 10 * dim)
    n_keep = min(10, n_samples)

    cur_params = params

    # Adaptive expansion loop
    for _round in range(max_expand + 1):
        # 1) Random search on small subset
        cand_costs: List[Tuple[float, Dict[str, Any]]] = []
        cand_costs.append((best_cost_small, dict(best_values)))

        for _ in range(n_samples):
            cand = _make_candidate(rng, cur_params)
            c = eval_values(cand, inst_small)
            cand_costs.append((c, cand))

        cand_costs.sort(key=lambda x: x[0])
        top = [c for _, c in cand_costs[:n_keep]]

        # 2) Refine top candidates on mid subset
        best_mid = None
        best_cost_mid = float("inf")
        for cand in top:
            refined, c_ref = _pattern_refine(rng, param_policy.fn, param_policy.params, cur_params, cand, inst_mid, n_rounds=3)
            # evaluate refined on mid subset
            c_mid = eval_values(refined, inst_mid)
            if c_mid < best_cost_mid:
                best_cost_mid = c_mid
                best_mid = refined

        if best_mid is None:
            best_mid = dict(best_values)
            best_cost_mid = eval_values(best_mid, inst_mid)

        # 3) Evaluate best on full train
        best_full_cost = eval_values(best_mid, train_instances)
        best_values = dict(best_mid)
        best_cost_small = eval_values(best_values, inst_small)

        # 4) Check if we are stuck at bounds; expand if so
        hits = _near_bounds(best_values, cur_params, frac=0.03)
        if not hits:
            # Done
            tuned_params = dict(best_values)
            tuned_code = replace_params_in_code(code, tuned_params)
            return TuneResult(tuned_code=tuned_code, tuned_params=tuned_params, train_avg=float(best_full_cost), status="ok")

        cur_params = _expand_params_bounds(cur_params, best_values, stats, hits)

    tuned_params = dict(best_values)
    tuned_code = replace_params_in_code(code, tuned_params)
    return TuneResult(tuned_code=tuned_code, tuned_params=tuned_params, train_avg=float(eval_values(best_values, train_instances)), status="ok_expanded")
