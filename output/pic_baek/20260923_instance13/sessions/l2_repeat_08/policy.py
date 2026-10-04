import math
import numpy as np
from scipy.stats import truncnorm


def _stratified_demands(mean, std, low, high, horizon, paths, seed):
    """Deterministic randomized Latin-hypercube demand paths."""
    a = (low - mean) / std
    b = (high - mean) / std
    rng = np.random.default_rng(seed)

    uniforms = np.empty((horizon, paths), dtype=float)
    ranks = np.arange(paths)
    midpoints = (ranks + 0.5) / paths
    for t in range(horizon):
        uniforms[t] = midpoints[rng.permutation(ranks)]

    return truncnorm.ppf(
        uniforms, a, b, loc=mean, scale=std
    )


def _evaluate_policies(params, targets, caps, demands, projected_demand):
    """Simulate many target/cap policies in parallel."""
    m = int(params["lifetime"])
    lead = int(params["lead_time"])
    n = m + lead - 1
    horizon = int(params["horizon"])
    backlog_limit = float(params["max_backlog"])
    discount = float(params["discount"])

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    targets = np.asarray(targets, dtype=float).reshape(-1, 1)
    caps = np.asarray(caps, dtype=float).reshape(-1, 1)

    policy_count = targets.shape[0]
    path_count = demands.shape[1]

    state = np.full(
        (policy_count, path_count, n),
        float(params["initial_component"]),
        dtype=float,
    )
    values = np.zeros((policy_count, path_count), dtype=float)

    factor = 1.0
    for t in range(horizon):
        observed = np.rint(state)

        # Project the observed state to the period in which an order placed
        # now arrives. Future orders are set to zero in this projection.
        projected_oldest = observed[..., 0]
        for j in range(lead):
            younger_sum = np.sum(
                observed[..., j + 2:j + m], axis=-1
            )
            projected_oldest = np.maximum(
                observed[..., j + 1]
                - np.maximum(0.0, projected_demand - projected_oldest),
                -backlog_limit - younger_sum,
            )

        projected_inventory = projected_oldest + np.sum(
            observed[..., lead + 1:n], axis=-1
        )

        order = np.floor(targets - projected_inventory + 0.5)
        order = np.maximum(0.0, np.minimum(caps, order))

        demand = demands[t][None, :]
        total_inventory = np.sum(state[..., :m], axis=-1)
        shortage = demand - total_inventory

        held = np.maximum(
            0.0,
            np.sum(state[..., 1:m], axis=-1)
            - np.maximum(0.0, demand - state[..., 0]),
        )

        period_cost = (
            purchase_cost * order
            + holding_cost * held
            + backlog_cost * np.maximum(0.0, shortage)
            + disposal_cost * np.maximum(0.0, state[..., 0] - demand)
            + lost_sales_cost
            * np.maximum(0.0, shortage - backlog_limit)
        )
        values += factor * period_cost

        new_oldest = np.maximum(
            state[..., 1]
            - np.maximum(0.0, demand - state[..., 0]),
            -backlog_limit - np.sum(state[..., 2:m], axis=-1),
        )
        state = np.concatenate(
            (new_oldest[..., None], state[..., 2:], order[..., None]),
            axis=-1,
        )

        factor *= discount

    return np.mean(values, axis=1)


def design(params):
    p = dict(params)

    m = int(p["lifetime"])
    lead = int(p["lead_time"])
    max_order = int(p["max_order"])
    backlog_limit = int(p["max_backlog"])
    horizon = int(p["horizon"])

    demand_mean = float(p["demand_mean"])
    demand_std = float(p["demand_std"])
    demand_low = float(p["demand_low"])
    demand_high = float(p["demand_high"])

    a = (demand_low - demand_mean) / demand_std
    b = (demand_high - demand_mean) / demand_std
    conditional_mean = float(
        truncnorm.mean(
            a, b, loc=demand_mean, scale=demand_std
        )
    )
    conditional_std = float(
        truncnorm.std(
            a, b, loc=demand_mean, scale=demand_std
        )
    )

    target_min = -float(backlog_limit)
    target_max = float(m) * demand_high

    # Coarse search over every possible recovery/order cap.
    coarse_targets = np.arange(
        target_min, target_max + 1.0e-9, 2.0
    )
    coarse_caps = np.arange(max_order + 1, dtype=int)

    cap_grid, target_grid = np.meshgrid(
        coarse_caps, coarse_targets, indexing="ij"
    )
    coarse_caps_flat = cap_grid.ravel()
    coarse_targets_flat = target_grid.ravel()

    coarse_demands = _stratified_demands(
        demand_mean,
        demand_std,
        demand_low,
        demand_high,
        horizon,
        12,
        17011,
    )
    coarse_scores = _evaluate_policies(
        p,
        coarse_targets_flat,
        coarse_caps_flat,
        coarse_demands,
        conditional_mean,
    )

    best_target_by_cap = np.empty(max_order + 1, dtype=float)
    best_score_by_cap = np.empty(max_order + 1, dtype=float)

    target_count = len(coarse_targets)
    for cap in range(max_order + 1):
        start = cap * target_count
        stop = start + target_count
        local = int(np.argmin(coarse_scores[start:stop]))
        idx = start + local
        best_target_by_cap[cap] = coarse_targets_flat[idx]
        best_score_by_cap[cap] = coarse_scores[idx]

    # Retain the best coarse caps, nearby caps, and several economically
    # meaningful caps to guard against coarse-search sampling error.
    promising_caps = set()
    cap_centers = list(
        np.argsort(best_score_by_cap)[:min(8, max_order + 1)]
    )

    special_caps = [
        0,
        max_order,
        min(max_order, 10),
        min(max_order, max(0, int(round(conditional_mean)))),
        min(
            max_order,
            max(
                0,
                int(math.ceil(conditional_mean + 2.0 * conditional_std)),
            ),
        ),
    ]
    cap_centers.extend(special_caps)

    for center in cap_centers:
        center = int(center)
        for cap in range(
            max(0, center - 1), min(max_order, center + 1) + 1
        ):
            promising_caps.add(cap)

    # Fine target search for the retained caps.
    fine_targets = []
    fine_caps = []
    for cap in sorted(promising_caps):
        if cap == 0:
            fine_targets.append(target_min)
            fine_caps.append(0)
            continue

        center = best_target_by_cap[cap]
        candidates = np.arange(center - 2.5, center + 2.5001, 0.25)
        candidates = np.clip(candidates, target_min, target_max)
        candidates = np.unique(candidates)

        fine_targets.extend(candidates.tolist())
        fine_caps.extend([cap] * len(candidates))

    fine_targets = np.asarray(fine_targets, dtype=float)
    fine_caps = np.asarray(fine_caps, dtype=int)

    fine_demands = _stratified_demands(
        demand_mean,
        demand_std,
        demand_low,
        demand_high,
        horizon,
        48,
        29123,
    )
    fine_scores = _evaluate_policies(
        p,
        fine_targets,
        fine_caps,
        fine_demands,
        conditional_mean,
    )

    # Form a diverse finalist set: globally good policies plus the best
    # policy for each retained cap.
    finalist_indices = set(
        np.argsort(fine_scores)[:min(50, len(fine_scores))].tolist()
    )
    for cap in promising_caps:
        indices = np.flatnonzero(fine_caps == cap)
        if len(indices):
            local = indices[int(np.argmin(fine_scores[indices]))]
            finalist_indices.add(int(local))

    finalist_indices = np.asarray(sorted(finalist_indices), dtype=int)
    finalist_targets = fine_targets[finalist_indices]
    finalist_caps = fine_caps[finalist_indices]

    final_demands = _stratified_demands(
        demand_mean,
        demand_std,
        demand_low,
        demand_high,
        horizon,
        192,
        41777,
    )
    final_scores = _evaluate_policies(
        p,
        finalist_targets,
        finalist_caps,
        final_demands,
        conditional_mean,
    )

    winner = int(np.argmin(final_scores))
    chosen_target = float(finalist_targets[winner])
    chosen_cap = int(finalist_caps[winner])

    n = m + lead - 1
    backlog_limit_float = float(backlog_limit)

    def compute_order_amount(state):
        # The supplied state is already rounded, but conversion to float
        # makes arithmetic consistent for Python and NumPy scalar inputs.
        z = tuple(float(v) for v in state)

        projected_oldest = z[0]
        for j in range(lead):
            younger_sum = sum(z[j + 2:j + m])
            projected_oldest = max(
                z[j + 1]
                - max(0.0, conditional_mean - projected_oldest),
                -backlog_limit_float - younger_sum,
            )

        projected_inventory = (
            projected_oldest + sum(z[lead + 1:n])
        )
        order = int(
            math.floor(chosen_target - projected_inventory + 0.5)
        )

        if order <= 0:
            return 0
        if order >= chosen_cap:
            return chosen_cap
        return order

    return compute_order_amount
