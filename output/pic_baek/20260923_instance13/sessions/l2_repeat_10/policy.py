import numpy as np
from scipy.stats import truncnorm


def design(params):
    m = int(params["lifetime"])
    lead = int(params["lead_time"])
    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    discount = float(params["discount"])
    horizon = int(params["horizon"])
    initial_component = float(params["initial_component"])

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    demand_mean = float(params["demand_mean"])
    demand_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])

    state_dim = m + lead - 1
    lower = (demand_low - demand_mean) / demand_std
    upper = (demand_high - demand_mean) / demand_std
    demand_distribution = truncnorm(
        lower,
        upper,
        loc=demand_mean,
        scale=demand_std,
    )
    truncated_mean = float(demand_distribution.mean())

    # A randomized Latin-hypercube panel gives accurate policy comparisons
    # with substantially fewer trajectories than ordinary Monte Carlo.
    simulation_horizon = min(horizon, 400)
    tail_start = max(0, simulation_horizon - 100)

    def make_demand_panel(number_of_paths, seed):
        rng = np.random.default_rng(seed)
        uniforms = np.empty((simulation_horizon, number_of_paths))
        for t in range(simulation_horizon):
            uniforms[t] = (
                rng.permutation(number_of_paths)
                + rng.random(number_of_paths)
            ) / number_of_paths
        return demand_distribution.ppf(uniforms)

    def unique_candidates(candidates):
        result = []
        seen = set()
        for candidate in candidates:
            candidate = tuple(float(x) for x in candidate)
            key = tuple(round(x, 10) for x in candidate)
            if key not in seen:
                seen.add(key)
                result.append(candidate)
        return result

    def evaluate_candidates(candidates, demands):
        candidates = np.asarray(candidates, dtype=float)
        targets = candidates[:, 0]
        forecasts = candidates[:, 1]
        gains = candidates[:, 2]

        candidate_count = len(candidates)
        path_count = demands.shape[1]

        states = np.full(
            (candidate_count, path_count, state_dim),
            initial_component,
            dtype=float,
        )
        objectives = np.zeros(candidate_count, dtype=float)
        tail_costs = np.zeros(candidate_count, dtype=float)
        discount_factor = 1.0

        for t in range(simulation_horizon):
            observed = np.rint(states)

            # Project the observed age inventory to the epoch at which the
            # present order will arrive. Future orders are set to zero.
            ages = observed[:, :, :m].copy()
            for k in range(lead):
                residual_demand = np.maximum(
                    0.0, forecasts[:, None] - ages[:, :, 0]
                )
                lower_bound = (
                    -max_backlog
                    - ages[:, :, 2:m].sum(axis=2)
                )
                new_oldest = np.maximum(
                    ages[:, :, 1] - residual_demand,
                    lower_bound,
                )

                ages[:, :, :-1] = ages[:, :, 1:]
                if k < lead - 1:
                    ages[:, :, -1] = observed[:, :, m + k]
                else:
                    ages[:, :, -1] = 0.0
                ages[:, :, 0] = new_oldest

            projected_inventory = ages.sum(axis=2)
            orders = np.rint(
                gains[:, None]
                * (targets[:, None] - projected_inventory)
            )
            orders = np.clip(orders, 0, max_order)

            demand = demands[t][None, :]
            age_inventory = states[:, :, :m]
            shortage = demand - age_inventory.sum(axis=2)

            period_cost = (
                purchase_cost * orders
                + holding_cost
                * np.maximum(
                    0.0,
                    states[:, :, 1:m].sum(axis=2)
                    - np.maximum(0.0, demand - states[:, :, 0]),
                )
                + backlog_cost * np.maximum(0.0, shortage)
                + disposal_cost
                * np.maximum(0.0, states[:, :, 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, shortage - max_backlog)
            )

            mean_period_cost = period_cost.mean(axis=1)
            objectives += discount_factor * mean_period_cost
            if t >= tail_start:
                tail_costs += mean_period_cost
            discount_factor *= discount

            residual_demand = np.maximum(
                0.0, demand - states[:, :, 0]
            )
            lower_bound = (
                -max_backlog
                - states[:, :, 2:m].sum(axis=2)
            )
            new_oldest = np.maximum(
                states[:, :, 1] - residual_demand,
                lower_bound,
            )

            states[:, :, :-1] = states[:, :, 1:]
            states[:, :, -1] = orders
            states[:, :, 0] = new_oldest

        # Beyond the simulated prefix, the system is effectively stationary.
        # Estimate the remaining finite-horizon cost from its recent average.
        if simulation_horizon < horizon:
            average_tail_cost = tail_costs / (
                simulation_horizon - tail_start
            )
            remaining_discount_mass = (
                discount ** simulation_horizon
                - discount ** horizon
            ) / (1.0 - discount)
            objectives += remaining_discount_mass * average_tail_cost

        return objectives

    first_panel = make_demand_panel(128, 918273)

    # First optimize the target for the standard projected-inventory policy.
    target_high = max_backlog + 12.0
    target_grid = np.arange(
        -max_backlog, target_high + 0.001, 1.0
    )
    first_candidates = [
        (target, truncated_mean, 1.0)
        for target in target_grid
    ]
    first_scores = evaluate_candidates(first_candidates, first_panel)
    base_target = float(target_grid[int(np.argmin(first_scores))])

    # Explore modest changes in the deterministic projection rate and in the
    # order adjustment gain. Target centers are shifted to preserve roughly
    # the same inventory-position threshold.
    second_candidates = []
    for forecast_offset in (-1.0, -0.5, 0.0, 0.5, 1.0):
        forecast = min(
            demand_high - 0.001,
            max(demand_low + 0.001,
                truncated_mean + forecast_offset),
        )
        for gain in (0.65, 0.8, 1.0, 1.2):
            center = (
                base_target
                - lead * (forecast - truncated_mean)
                + truncated_mean * (1.0 / gain - 1.0)
            )
            for displacement in (-4.0, -2.0, -1.0, 0.0,
                                 1.0, 2.0, 4.0):
                second_candidates.append(
                    (center + displacement, forecast, gain)
                )

    second_candidates = unique_candidates(second_candidates)
    second_scores = evaluate_candidates(
        second_candidates, first_panel
    )

    # Keep the best target found for each forecast/gain structure.
    structures = {}
    for candidate, score in zip(second_candidates, second_scores):
        target, forecast, gain = candidate
        key = (round(forecast, 10), round(gain, 10))
        if key not in structures or score < structures[key][0]:
            structures[key] = (
                float(score), target, forecast, gain
            )

    baseline_key = (round(truncated_mean, 10), 1.0)
    baseline_entry = (
        float(np.min(first_scores)),
        base_target,
        truncated_mean,
        1.0,
    )
    if (
        baseline_key not in structures
        or baseline_entry[0] < structures[baseline_key][0]
    ):
        structures[baseline_key] = baseline_entry

    best_structures = sorted(
        structures.values(), key=lambda item: item[0]
    )[:6]

    # Refine targets on an independent, larger panel.
    final_candidates = []
    for _, center, forecast, gain in best_structures:
        for displacement in np.arange(-2.0, 2.001, 0.25):
            final_candidates.append(
                (center + displacement, forecast, gain)
            )

    final_candidates = unique_candidates(final_candidates)
    second_panel = make_demand_panel(256, 271828)
    final_scores = evaluate_candidates(
        final_candidates, second_panel
    )
    target, forecast, gain = final_candidates[
        int(np.argmin(final_scores))
    ]

    def compute_order_amount(state):
        observed = [float(value) for value in state]
        ages = observed[:m]

        # Project to the arrival epoch using the fixed demand forecast and the
        # already-outstanding orders. The new order itself is excluded.
        for k in range(lead):
            residual_demand = max(0.0, forecast - ages[0])
            lower_bound = -max_backlog - sum(ages[2:])
            new_oldest = max(
                ages[1] - residual_demand,
                lower_bound,
            )
            incoming = observed[m + k] if k < lead - 1 else 0.0
            ages = [new_oldest] + ages[2:] + [incoming]

        projected_inventory = sum(ages)
        order = int(np.rint(gain * (target - projected_inventory)))

        if order < 0:
            return 0
        if order > max_order:
            return max_order
        return order

    return compute_order_amount
