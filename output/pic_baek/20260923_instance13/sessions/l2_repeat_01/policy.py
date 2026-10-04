import math
import numpy as np
from scipy.stats import truncnorm, qmc


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    horizon = int(params["horizon"])
    discount = float(params["discount"])
    initial_component = float(params["initial_component"])
    state_length = m + lead_time - 1

    demand_mean = float(params["demand_mean"])
    demand_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    a = (demand_low - demand_mean) / demand_std
    b = (demand_high - demand_mean) / demand_std
    truncated_mean = float(
        truncnorm.mean(a, b, loc=demand_mean, scale=demand_std)
    )
    truncated_std = float(
        truncnorm.std(a, b, loc=demand_mean, scale=demand_std)
    )

    # For the more heavily discounted instances the omitted tail is negligible.
    tail_horizon = int(math.ceil(math.log(1e-7) / math.log(discount)))
    simulation_horizon = min(horizon, max(250, tail_horizon))

    # Deterministic randomized QMC scenarios make design reproducible and
    # provide common random numbers for all candidate policies.
    sampler = qmc.Sobol(d=simulation_horizon, scramble=True, seed=1729)
    uniforms = sampler.random_base2(6).T
    uniforms = np.clip(uniforms, 1e-12, 1.0 - 1e-12)
    demand_scenarios = truncnorm.ppf(
        uniforms, a, b, loc=demand_mean, scale=demand_std
    )

    def evaluate_candidates(targets, waste_weights, forecasts, demands):
        targets = np.asarray(targets, dtype=float)
        waste_weights = np.asarray(waste_weights, dtype=float)
        forecasts = np.asarray(forecasts, dtype=float)

        candidate_count = targets.size
        replication_count = demands.shape[1]

        states = np.full(
            (candidate_count, replication_count, state_length),
            initial_component,
            dtype=float,
        )
        objective = np.zeros(candidate_count, dtype=float)

        target_column = targets[:, None]
        waste_column = waste_weights[:, None]
        forecast_column = forecasts[:, None]

        discount_factor = 1.0

        for period in range(simulation_horizon):
            rounded = np.rint(states)

            # Project the currently known inventory and pipeline to the time at
            # which the order selected now will become available.
            projected = rounded.copy()
            for _ in range(lead_time):
                next_projected = np.empty_like(projected)
                shortage = np.maximum(
                    0.0, forecast_column - projected[:, :, 0]
                )
                lower_bound = (
                    -max_backlog
                    - np.sum(projected[:, :, 2:m], axis=2)
                )
                next_projected[:, :, 0] = np.maximum(
                    projected[:, :, 1] - shortage, lower_bound
                )
                next_projected[:, :, 1:-1] = projected[:, :, 2:]
                next_projected[:, :, -1] = 0.0
                projected = next_projected

            # Estimate inventory in the projected state that would expire
            # before it can be useful. The fitted weight lets setup choose
            # whether this correction improves the instance.
            future = projected.copy()
            predicted_waste = np.zeros(
                (candidate_count, replication_count), dtype=float
            )
            for _ in range(m):
                predicted_waste += np.maximum(
                    0.0, future[:, :, 0] - forecast_column
                )
                next_future = np.empty_like(future)
                shortage = np.maximum(
                    0.0, forecast_column - future[:, :, 0]
                )
                lower_bound = (
                    -max_backlog - np.sum(future[:, :, 2:m], axis=2)
                )
                next_future[:, :, 0] = np.maximum(
                    future[:, :, 1] - shortage, lower_bound
                )
                next_future[:, :, 1:-1] = future[:, :, 2:]
                next_future[:, :, -1] = 0.0
                future = next_future

            effective_inventory = (
                np.sum(projected[:, :, :m], axis=2)
                - waste_column * predicted_waste
            )
            orders = np.clip(
                np.rint(target_column - effective_inventory),
                0,
                max_order,
            )

            demand = demands[period][None, :]
            total_inventory = np.sum(states[:, :, :m], axis=2)
            unmet = demand - total_inventory

            period_cost = (
                purchase_cost * orders
                + holding_cost
                * np.maximum(
                    0.0,
                    np.sum(states[:, :, 1:m], axis=2)
                    - np.maximum(0.0, demand - states[:, :, 0]),
                )
                + backlog_cost * np.maximum(0.0, unmet)
                + disposal_cost
                * np.maximum(0.0, states[:, :, 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, unmet - max_backlog)
            )
            objective += discount_factor * np.mean(period_cost, axis=1)
            discount_factor *= discount

            next_states = np.empty_like(states)
            residual_demand = np.maximum(
                0.0, demand - states[:, :, 0]
            )
            lower_bound = (
                -max_backlog - np.sum(states[:, :, 2:m], axis=2)
            )
            next_states[:, :, 0] = np.maximum(
                states[:, :, 1] - residual_demand, lower_bound
            )
            next_states[:, :, 1:-1] = states[:, :, 2:]
            next_states[:, :, -1] = orders
            states = next_states

        return objective

    # Forecast perturbations give several approximations to the survival of
    # old inventory through the lead time. Waste correction is either enabled
    # or disabled; its usefulness depends strongly on lifetime and demand.
    structures = []
    for beta in (-0.30, 0.0, 0.30):
        forecast = float(
            np.clip(
                truncated_mean + beta * truncated_std,
                demand_low,
                demand_high,
            )
        )
        structures.append((0.0, forecast))
        structures.append((1.0, forecast))

    upper_target = float(m * demand_high)
    coarse_grid = np.arange(
        -max_backlog, upper_target + 0.1, 1.0, dtype=float
    )

    coarse_targets = []
    coarse_weights = []
    coarse_forecasts = []
    for weight, forecast in structures:
        coarse_targets.extend(coarse_grid)
        coarse_weights.extend([weight] * coarse_grid.size)
        coarse_forecasts.extend([forecast] * coarse_grid.size)

    coarse_values = evaluate_candidates(
        coarse_targets,
        coarse_weights,
        coarse_forecasts,
        demand_scenarios[:, :32],
    )

    coarse_targets_array = np.asarray(coarse_targets)
    centers = []
    offset = 0
    for _ in structures:
        section = slice(offset, offset + coarse_grid.size)
        local_index = int(np.argmin(coarse_values[section]))
        centers.append(float(coarse_targets_array[section][local_index]))
        offset += coarse_grid.size

    # Refine each structural candidate near its own coarse optimum.
    fine_targets = []
    fine_weights = []
    fine_forecasts = []
    refinement_offsets = np.arange(-1.5, 1.5001, 0.1)

    for (weight, forecast), center in zip(structures, centers):
        local_grid = np.unique(
            np.clip(
                center + refinement_offsets,
                -max_backlog,
                upper_target,
            )
        )
        fine_targets.extend(local_grid)
        fine_weights.extend([weight] * local_grid.size)
        fine_forecasts.extend([forecast] * local_grid.size)

    fine_values = evaluate_candidates(
        fine_targets,
        fine_weights,
        fine_forecasts,
        demand_scenarios,
    )
    best = int(np.argmin(fine_values))

    selected_target = float(fine_targets[best])
    selected_waste_weight = float(fine_weights[best])
    selected_forecast = float(fine_forecasts[best])

    def compute_order_amount(state):
        projected = [float(value) for value in state]

        # Forecast to the order's arrival epoch, appending zero in place of
        # the order whose amount is currently being computed.
        for _ in range(lead_time):
            residual = max(
                0.0, selected_forecast - projected[0]
            )
            lower_bound = (
                -max_backlog - sum(projected[2:m])
            )
            first = max(projected[1] - residual, lower_bound)
            projected = [first] + projected[2:] + [0.0]

        predicted_waste = 0.0
        if selected_waste_weight != 0.0:
            future = projected.copy()
            for _ in range(m):
                predicted_waste += max(
                    0.0, future[0] - selected_forecast
                )
                residual = max(
                    0.0, selected_forecast - future[0]
                )
                lower_bound = -max_backlog - sum(future[2:m])
                first = max(future[1] - residual, lower_bound)
                future = [first] + future[2:] + [0.0]

        effective_inventory = (
            sum(projected[:m])
            - selected_waste_weight * predicted_waste
        )
        order = int(np.rint(selected_target - effective_inventory))

        if order < 0:
            return 0
        if order > max_order:
            return max_order
        return order

    return compute_order_amount
