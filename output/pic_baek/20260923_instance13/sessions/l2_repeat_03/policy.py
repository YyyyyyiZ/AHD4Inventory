import math
import numpy as np
from scipy.stats import truncnorm, qmc


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    state_length = m + lead_time - 1

    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    discount = float(params["discount"])
    initial_component = float(params["initial_component"])

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    parent_mean = float(params["demand_mean"])
    parent_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])

    trunc_a = (demand_low - parent_mean) / parent_std
    trunc_b = (demand_high - parent_mean) / parent_std

    mean_demand = float(
        truncnorm.mean(
            trunc_a,
            trunc_b,
            loc=parent_mean,
            scale=parent_std,
        )
    )

    # Discounted contributions beyond this point are negligible for policy
    # selection, while the actual returned policy remains stationary.
    simulation_horizon = min(
        int(params["horizon"]),
        max(300, int(math.ceil(math.log(1.0e-3) / math.log(discount)))),
    )

    simulation_replications = 128
    uniforms = qmc.Sobol(
        d=simulation_horizon,
        scramble=True,
        seed=1729,
    ).random_base2(7)

    simulated_demands = truncnorm.ppf(
        uniforms,
        trunc_a,
        trunc_b,
        loc=parent_mean,
        scale=parent_std,
    ).T

    def evaluate_policies(targets, forecasts, gains, replications):
        targets = np.asarray(targets, dtype=float)
        forecasts = np.asarray(forecasts, dtype=float)
        gains = np.asarray(gains, dtype=float)

        policy_count = targets.size
        states = np.full(
            (policy_count, replications, state_length),
            initial_component,
            dtype=float,
        )
        values = np.zeros((policy_count, replications), dtype=float)
        discount_factor = 1.0

        for period in range(simulation_horizon):
            # Project the rounded observed state to the time at which the
            # current order would become usable. The trial order and all later
            # orders are initially set to zero, so its required amount can be
            # inferred from the projected inventory.
            projected = np.rint(states).copy()

            for _ in range(lead_time):
                projected_first = np.maximum(
                    projected[..., 1]
                    - np.maximum(
                        0.0,
                        forecasts[:, None] - projected[..., 0],
                    ),
                    -max_backlog
                    - np.sum(projected[..., 2:m], axis=-1),
                )

                projected[..., :-1] = projected[..., 1:]
                projected[..., -1] = 0.0
                projected[..., 0] = projected_first

            projected_inventory = np.sum(projected[..., :m], axis=-1)

            orders = np.clip(
                np.floor(
                    gains[:, None]
                    * (targets[:, None] - projected_inventory)
                    + 0.5
                ),
                0,
                max_order,
            )

            demand = simulated_demands[period, :replications][None, :]
            total_inventory = np.sum(states[..., :m], axis=-1)
            unmet = demand - total_inventory

            period_cost = (
                purchase_cost * orders
                + holding_cost
                * np.maximum(
                    0.0,
                    np.sum(states[..., 1:m], axis=-1)
                    - np.maximum(0.0, demand - states[..., 0]),
                )
                + backlog_cost * np.maximum(0.0, unmet)
                + disposal_cost * np.maximum(0.0, states[..., 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, unmet - max_backlog)
            )

            values += discount_factor * period_cost

            next_first = np.maximum(
                states[..., 1]
                - np.maximum(0.0, demand - states[..., 0]),
                -max_backlog
                - np.sum(states[..., 2:m], axis=-1),
            )

            states[..., :-1] = states[..., 1:]
            states[..., -1] = orders
            states[..., 0] = next_first

            discount_factor *= discount

        return np.mean(values, axis=1)

    # Search over a family of projected-inventory policies. The demand
    # forecast multiplier compensates for nonlinear depletion and aging,
    # while the gain controls how aggressively inventory deviations are
    # corrected.
    lower_target = -max_backlog
    upper_target = min(50.0, 10.0 * m)
    coarse_targets = np.linspace(lower_target, upper_target, 33)
    coarse_spacing = coarse_targets[1] - coarse_targets[0]

    forecast_multipliers = (0.8, 0.9, 1.0, 1.1, 1.2)
    candidate_gains = (0.5, 0.75, 1.0, 1.25)

    coarse_candidates = [
        (target, mean_demand * multiplier, gain)
        for multiplier in forecast_multipliers
        for gain in candidate_gains
        for target in coarse_targets
    ]

    coarse_target_array, coarse_forecast_array, coarse_gain_array = map(
        np.asarray, zip(*coarse_candidates)
    )

    coarse_values = evaluate_policies(
        coarse_target_array,
        coarse_forecast_array,
        coarse_gain_array,
        32,
    )

    refined_candidates = []
    block_size = coarse_targets.size
    parameter_block_count = (
        len(forecast_multipliers) * len(candidate_gains)
    )

    for block in range(parameter_block_count):
        start = block * block_size
        stop = start + block_size
        best_index = start + int(np.argmin(coarse_values[start:stop]))

        center = float(coarse_target_array[best_index])
        forecast = float(coarse_forecast_array[best_index])
        gain = float(coarse_gain_array[best_index])

        for offset in np.linspace(-coarse_spacing, coarse_spacing, 11):
            refined_target = min(
                upper_target,
                max(lower_target, center + float(offset)),
            )
            refined_candidates.append(
                (refined_target, forecast, gain)
            )

    refined_target_array, refined_forecast_array, refined_gain_array = map(
        np.asarray, zip(*refined_candidates)
    )

    refined_values = evaluate_policies(
        refined_target_array,
        refined_forecast_array,
        refined_gain_array,
        simulation_replications,
    )

    best = int(np.argmin(refined_values))
    target = float(refined_target_array[best])
    forecast = float(refined_forecast_array[best])
    gain = float(refined_gain_array[best])

    def compute_order_amount(state):
        projected = [float(component) for component in state]

        for _ in range(lead_time):
            projected_first = max(
                projected[1] - max(0.0, forecast - projected[0]),
                -max_backlog - sum(projected[2:m]),
            )
            projected = [projected_first] + projected[2:] + [0.0]

        projected_inventory = sum(projected[:m])
        order = math.floor(
            gain * (target - projected_inventory) + 0.5
        )

        if order <= 0:
            return 0
        if order >= max_order:
            return max_order
        return int(order)

    return compute_order_amount
