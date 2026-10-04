import math
import numpy as np
from scipy.stats import truncnorm


def design(params):
    m = int(params["lifetime"])
    lead = int(params["lead_time"])
    state_len = m + lead - 1
    max_backlog = float(params["max_backlog"])
    max_order = int(params["max_order"])
    discount = float(params["discount"])
    horizon = int(params["horizon"])

    demand_mean = float(params["demand_mean"])
    demand_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])

    demand_rv = truncnorm(
        (demand_low - demand_mean) / demand_std,
        (demand_high - demand_mean) / demand_std,
        loc=demand_mean,
        scale=demand_std,
    )
    conditional_mean = float(demand_rv.mean())
    conditional_std = float(demand_rv.std())

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    initial_component = float(params["initial_component"])

    # Candidate format:
    # (family, target, deterministic_forecast, oldest_weight,
    #  backlog_weight, feedback_gain, structural_id)
    #
    # family 0: projected-inventory-level policy
    # family 1: inventory-position policy
    # family 2: constant-order policy
    candidates = []
    structural_id = 0

    useful_upper = min(
        m * demand_high,
        demand_high + 4.0 * conditional_std * math.sqrt(lead),
    )

    if max_backlog > 10.0:
        negative_targets = np.arange(-max_backlog, -10.000001, 5.0)
    else:
        negative_targets = np.empty(0)
    main_targets = np.arange(-10.0, useful_upper + 1.0e-9, 2.0)
    projected_targets = np.unique(
        np.concatenate((negative_targets, main_targets, [useful_upper]))
    )

    forecast_scale = conditional_std / math.sqrt(lead)
    for forecast_multiplier in (-2.0, -1.0, 0.0, 1.0, 2.0):
        forecast = conditional_mean + forecast_multiplier * forecast_scale
        forecast = min(demand_high - 0.001, max(demand_low + 0.001, forecast))

        for oldest_weight in (0.5, 1.0):
            for backlog_weight in (0.5, 1.0):
                for target in projected_targets:
                    candidates.append(
                        (
                            0,
                            float(target),
                            float(forecast),
                            oldest_weight,
                            backlog_weight,
                            1.0,
                            structural_id,
                        )
                    )
                structural_id += 1

    inventory_position_upper = min(
        150.0,
        demand_high * (lead + 1)
        + 4.0 * conditional_std * math.sqrt(lead + 1),
    )
    inventory_position_targets = np.arange(
        -max_backlog, inventory_position_upper + 1.0e-9, 4.0
    )
    inventory_position_targets = np.unique(
        np.concatenate((inventory_position_targets, [inventory_position_upper]))
    )

    inventory_position_id = structural_id
    for target in inventory_position_targets:
        candidates.append(
            (
                1,
                float(target),
                conditional_mean,
                1.0,
                1.0,
                1.0,
                inventory_position_id,
            )
        )
    structural_id += 1

    constant_id = structural_id
    maximum_constant_order = min(max_order, int(math.ceil(demand_high)))
    for order in range(maximum_constant_order + 1):
        candidates.append(
            (
                2,
                float(order),
                conditional_mean,
                1.0,
                1.0,
                1.0,
                constant_id,
            )
        )
    structural_id += 1

    def simulate(policy_candidates, trajectory_count, seed, simulation_horizon):
        count = len(policy_candidates)
        data = np.asarray([candidate[:6] for candidate in policy_candidates],
                          dtype=float)

        family = data[:, 0].astype(np.int8)
        target = data[:, 1, None]
        forecast = data[:, 2, None]
        oldest_weight = data[:, 3, None]
        backlog_weight = data[:, 4, None]
        gain = data[:, 5, None]

        projected_mask = family == 0
        position_mask = family == 1
        constant_mask = family == 2

        rng = np.random.default_rng(seed)
        half_count = (trajectory_count + 1) // 2
        uniforms = rng.random((simulation_horizon, half_count))
        uniforms = np.concatenate((uniforms, 1.0 - uniforms), axis=1)
        uniforms = uniforms[:, :trajectory_count]
        demands = demand_rv.ppf(uniforms)

        states = np.full(
            (count, trajectory_count, state_len),
            initial_component,
            dtype=float,
        )
        values = np.zeros(count, dtype=float)
        discount_factor = 1.0

        for period in range(simulation_horizon):
            rounded = np.rint(states)

            # Project the rounded state to the receipt epoch of the order
            # currently being selected. Orders not yet selected are set to zero.
            projected = rounded.copy()
            for _ in range(lead):
                new_oldest = np.maximum(
                    projected[:, :, 1]
                    - np.maximum(0.0, forecast - projected[:, :, 0]),
                    -max_backlog
                    - np.sum(projected[:, :, 2:m], axis=2),
                )
                projected[:, :, :-1] = projected[:, :, 1:]
                projected[:, :, 0] = new_oldest
                projected[:, :, -1] = 0.0

            metric = (
                np.sum(projected[:, :, 1:m], axis=2)
                + oldest_weight * np.maximum(projected[:, :, 0], 0.0)
                + backlog_weight * np.minimum(projected[:, :, 0], 0.0)
            )
            orders = np.clip(
                np.floor(gain * (target - metric) + 0.5),
                0.0,
                max_order,
            )

            if np.any(position_mask):
                position_metric = np.sum(
                    rounded[position_mask], axis=2
                )
                orders[position_mask] = np.clip(
                    np.floor(
                        gain[position_mask]
                        * (target[position_mask] - position_metric)
                        + 0.5
                    ),
                    0.0,
                    max_order,
                )

            if np.any(constant_mask):
                orders[constant_mask] = np.clip(
                    np.floor(target[constant_mask] + 0.5),
                    0.0,
                    max_order,
                )

            demand = demands[period][None, :]
            total_inventory = np.sum(states[:, :, :m], axis=2)
            shortage = demand - total_inventory

            period_cost = (
                purchase_cost * orders
                + holding_cost
                * np.maximum(
                    0.0,
                    np.sum(states[:, :, 1:m], axis=2)
                    - np.maximum(0.0, demand - states[:, :, 0]),
                )
                + backlog_cost * np.maximum(0.0, shortage)
                + disposal_cost
                * np.maximum(0.0, states[:, :, 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, shortage - max_backlog)
            )

            values += discount_factor * np.mean(period_cost, axis=1)

            new_oldest = np.maximum(
                states[:, :, 1]
                - np.maximum(0.0, demand - states[:, :, 0]),
                -max_backlog - np.sum(states[:, :, 2:m], axis=2),
            )
            states[:, :, :-1] = states[:, :, 1:]
            states[:, :, 0] = new_oldest
            states[:, :, -1] = orders

            discount_factor *= discount

        return values

    coarse_horizon = min(
        horizon,
        max(
            lead + m + 5,
            int(math.ceil(math.log(0.005) / math.log(discount))),
        ),
    )
    fine_horizon = min(
        horizon,
        max(
            lead + m + 5,
            int(math.ceil(math.log(0.0005) / math.log(discount))),
        ),
    )

    coarse_values = simulate(
        candidates,
        trajectory_count=24,
        seed=137,
        simulation_horizon=coarse_horizon,
    )

    # Keep the best target for each structural parameter combination, then
    # refine both its target and its feedback gain.
    refined_candidates = []
    target_offsets = (-4.0, -2.0, -0.5, 0.0, 0.5, 2.0, 4.0)
    feedback_gains = (0.75, 1.0, 1.25)

    for sid in range(structural_id):
        indices = [
            i for i, candidate in enumerate(candidates)
            if candidate[6] == sid
        ]
        best_index = indices[int(np.argmin(coarse_values[indices]))]
        base = candidates[best_index]

        if base[0] in (0, 1):
            for feedback_gain in feedback_gains:
                for offset in target_offsets:
                    refined_candidates.append(
                        (
                            base[0],
                            base[1] + offset,
                            base[2],
                            base[3],
                            base[4],
                            feedback_gain,
                            base[6],
                        )
                    )

    # Always validate every sensible constant order, including no ordering.
    for order in range(maximum_constant_order + 1):
        refined_candidates.append(
            (
                2,
                float(order),
                conditional_mean,
                1.0,
                1.0,
                1.0,
                constant_id,
            )
        )

    refined_candidates = list(dict.fromkeys(refined_candidates))

    validation_values = simulate(
        refined_candidates,
        trajectory_count=64,
        seed=821,
        simulation_horizon=fine_horizon,
    )

    finalist_count = min(20, len(refined_candidates))
    finalist_indices = np.argsort(validation_values)[:finalist_count]
    finalists = [refined_candidates[i] for i in finalist_indices]

    finalist_values = simulate(
        finalists,
        trajectory_count=192,
        seed=1931,
        simulation_horizon=fine_horizon,
    )

    # Combine the two independent estimates for the finalists.
    combined_values = (
        64.0 * validation_values[finalist_indices]
        + 192.0 * finalist_values
    ) / 256.0
    chosen = finalists[int(np.argmin(combined_values))]

    (
        chosen_family,
        chosen_target,
        chosen_forecast,
        chosen_oldest_weight,
        chosen_backlog_weight,
        chosen_gain,
        _,
    ) = chosen

    def compute_order_amount(state):
        rounded = np.asarray(state, dtype=float)

        if chosen_family == 2:
            return int(
                min(
                    max_order,
                    max(0, math.floor(chosen_target + 0.5)),
                )
            )

        if chosen_family == 1:
            raw_order = chosen_gain * (
                chosen_target - float(np.sum(rounded))
            )
            return int(
                min(max_order, max(0, math.floor(raw_order + 0.5)))
            )

        projected = rounded.copy()
        for _ in range(lead):
            new_oldest = max(
                projected[1]
                - max(0.0, chosen_forecast - projected[0]),
                -max_backlog - float(np.sum(projected[2:m])),
            )
            projected[:-1] = projected[1:]
            projected[0] = new_oldest
            projected[-1] = 0.0

        metric = (
            float(np.sum(projected[1:m]))
            + chosen_oldest_weight * max(projected[0], 0.0)
            + chosen_backlog_weight * min(projected[0], 0.0)
        )
        raw_order = chosen_gain * (chosen_target - metric)
        return int(
            min(max_order, max(0, math.floor(raw_order + 0.5)))
        )

    return compute_order_amount
