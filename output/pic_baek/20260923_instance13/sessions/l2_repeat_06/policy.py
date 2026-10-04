import math
import numpy as np
from scipy.stats import truncnorm


def _policy_values(
    m, lead_time, max_order, max_backlog, discount,
    purchase_cost, holding_cost, backlog_cost,
    disposal_cost, lost_sales_cost, initial_component,
    distribution, projection_demands, targets, gains,
    replications, horizon, seed
):
    projection_demands = np.asarray(projection_demands, dtype=float)
    targets = np.asarray(targets, dtype=float)
    gains = np.asarray(gains, dtype=float)
    candidate_count = targets.size

    rng = np.random.default_rng(seed)

    # Independently shuffled stratified samples in every period.
    uniforms = (
        np.arange(replications, dtype=float)[:, None]
        + rng.random((replications, horizon))
    ) / replications
    for t in range(horizon):
        rng.shuffle(uniforms[:, t])
    demands = distribution.ppf(uniforms)

    state_length = m + lead_time - 1
    states = np.full(
        (candidate_count, replications, state_length),
        float(initial_component),
        dtype=float,
    )
    values = np.zeros(candidate_count, dtype=float)
    discount_factor = 1.0

    for t in range(horizon):
        # Project the rounded observed state to the arrival epoch of the
        # order currently being selected. Future, not-yet-selected orders
        # are set to zero in this projection.
        projected = np.rint(states)
        for _ in range(lead_time):
            projected_first = np.maximum(
                projected[:, :, 1]
                - np.maximum(
                    0.0,
                    projection_demands[:, None] - projected[:, :, 0],
                ),
                -max_backlog - np.sum(projected[:, :, 2:m], axis=2),
            )
            projected[:, :, :-1] = projected[:, :, 1:]
            projected[:, :, 0] = projected_first
            projected[:, :, -1] = 0.0

        projected_inventory = np.sum(projected[:, :, :m], axis=2)
        orders = np.clip(
            np.rint(
                gains[:, None]
                * (targets[:, None] - projected_inventory)
            ),
            0.0,
            max_order,
        )

        demand = demands[:, t][None, :]
        unmet = demand - np.sum(states[:, :, :m], axis=2)

        period_cost = (
            purchase_cost * orders
            + holding_cost
            * np.maximum(
                0.0,
                np.sum(states[:, :, 1:m], axis=2)
                - np.maximum(0.0, demand - states[:, :, 0]),
            )
            + backlog_cost * np.maximum(0.0, unmet)
            + disposal_cost * np.maximum(0.0, states[:, :, 0] - demand)
            + lost_sales_cost
            * np.maximum(0.0, unmet - max_backlog)
        )
        values += discount_factor * np.mean(period_cost, axis=1)

        next_first = np.maximum(
            states[:, :, 1]
            - np.maximum(0.0, demand - states[:, :, 0]),
            -max_backlog - np.sum(states[:, :, 2:m], axis=2),
        )
        states[:, :, :-1] = states[:, :, 1:]
        states[:, :, 0] = next_first
        states[:, :, -1] = orders

        discount_factor *= discount

    return values


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    max_order = int(params["max_order"])
    max_backlog = int(params["max_backlog"])

    discount = float(params["discount"])
    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    initial_component = float(params["initial_component"])

    demand_mean = float(params["demand_mean"])
    demand_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])
    full_horizon = int(params["horizon"])

    distribution = truncnorm(
        (demand_low - demand_mean) / demand_std,
        (demand_high - demand_mean) / demand_std,
        loc=demand_mean,
        scale=demand_std,
    )
    truncated_mean = float(distribution.mean())
    truncated_std = float(distribution.std())

    # Terms beyond this horizon carry less than 1e-4 of the undiscounted
    # relative weight. The actual policy remains stationary.
    search_horizon = min(
        full_horizon,
        max(
            1,
            int(math.ceil(math.log(1.0e-4) / math.log(discount))),
        ),
    )

    common_args = (
        m,
        lead_time,
        max_order,
        max_backlog,
        discount,
        purchase_cost,
        holding_cost,
        backlog_cost,
        disposal_cost,
        lost_sales_cost,
        initial_component,
        distribution,
    )

    target_low = -float(max_backlog)
    target_high = min(
        float(m) * demand_high,
        float(m) * max_order,
    )

    # Coarse search over the projected demand, correction gain, and
    # projected-inventory target.
    coarse_projection_demands = np.clip(
        truncated_mean
        + truncated_std * np.array([-0.75, -0.25, 0.25, 0.75]),
        demand_low + 1.0e-8,
        demand_high - 1.0e-8,
    )
    coarse_gains = (0.65, 0.90, 1.15, 1.40)
    coarse_targets = np.linspace(target_low, target_high, 21)
    target_step = (target_high - target_low) / 20.0

    coarse_candidates = []
    for projected_demand in coarse_projection_demands:
        for gain in coarse_gains:
            for target in coarse_targets:
                coarse_candidates.append(
                    (float(projected_demand), float(target), float(gain))
                )

    coarse_d, coarse_t, coarse_g = map(
        np.asarray, zip(*coarse_candidates)
    )
    coarse_values = _policy_values(
        *common_args,
        coarse_d,
        coarse_t,
        coarse_g,
        40,
        search_horizon,
        19471,
    )

    # Recheck the best target and its neighbors for every (demand, gain)
    # pair using an independent, larger scenario set.
    shortlist = []
    targets_per_pair = len(coarse_targets)
    pair_count = (
        len(coarse_projection_demands) * len(coarse_gains)
    )
    for pair in range(pair_count):
        start = pair * targets_per_pair
        stop = start + targets_per_pair
        local_best = int(np.argmin(coarse_values[start:stop]))
        for offset in (-1, 0, 1):
            local_index = min(
                targets_per_pair - 1,
                max(0, local_best + offset),
            )
            shortlist.append(coarse_candidates[start + local_index])

    short_d, short_t, short_g = map(np.asarray, zip(*shortlist))
    shortlist_values = _policy_values(
        *common_args,
        short_d,
        short_t,
        short_g,
        72,
        search_horizon,
        51631,
    )
    center_index = int(np.argmin(shortlist_values))
    center_d, center_t, center_g = shortlist[center_index]

    # Local refinement.
    refined_candidates = []
    refined_demands = np.clip(
        center_d
        + truncated_std * np.array([-0.25, 0.0, 0.25]),
        demand_low + 1.0e-8,
        demand_high - 1.0e-8,
    )
    refined_gains = np.clip(
        center_g + np.array([-0.15, 0.0, 0.15]),
        0.35,
        1.75,
    )
    refined_targets = np.clip(
        center_t
        + target_step * np.linspace(-1.5, 1.5, 15),
        target_low,
        target_high,
    )

    for projected_demand in refined_demands:
        for gain in refined_gains:
            for target in refined_targets:
                refined_candidates.append(
                    (float(projected_demand), float(target), float(gain))
                )

    refined_d, refined_t, refined_g = map(
        np.asarray, zip(*refined_candidates)
    )
    refined_values = _policy_values(
        *common_args,
        refined_d,
        refined_t,
        refined_g,
        64,
        search_horizon,
        83729,
    )
    best_index = int(np.argmin(refined_values))
    policy_demand, policy_target, policy_gain = refined_candidates[best_index]

    def compute_order_amount(state):
        projected = [float(v) for v in state]

        for _ in range(lead_time):
            residual_demand = max(
                0.0, policy_demand - projected[0]
            )
            next_first = max(
                projected[1] - residual_demand,
                -max_backlog - sum(projected[2:m]),
            )
            projected = [next_first] + projected[2:] + [0.0]

        projected_inventory = sum(projected[:m])
        order = int(
            np.rint(
                policy_gain
                * (policy_target - projected_inventory)
            )
        )
        if order < 0:
            return 0
        if order > max_order:
            return max_order
        return order

    return compute_order_amount
