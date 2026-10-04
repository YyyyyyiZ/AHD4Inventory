import math
import numpy as np
from scipy.special import ndtr, ndtri
from scipy.stats import truncnorm


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    n = m + lead_time - 1

    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    discount = float(params["discount"])

    demand_loc = float(params["demand_mean"])
    demand_scale = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])

    a = (demand_low - demand_loc) / demand_scale
    b = (demand_high - demand_loc) / demand_scale

    demand_mean = float(
        truncnorm.mean(
            a, b, loc=demand_loc, scale=demand_scale
        )
    )
    demand_sd = float(
        truncnorm.std(
            a, b, loc=demand_loc, scale=demand_scale
        )
    )

    cdf_a = float(ndtr(a))
    cdf_b = float(ndtr(b))

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    initial_component = float(params["initial_component"])
    horizon = int(params["horizon"])

    def simulate(targets, alphas, gains, replications, periods, seed):
        targets = np.asarray(targets, dtype=float)
        alphas = np.asarray(alphas, dtype=float)
        gains = np.asarray(gains, dtype=float)
        candidate_count = targets.size

        rng = np.random.default_rng(seed)

        # Period-wise stratification gives accurate demand marginals with
        # relatively few trajectories.
        uniforms = np.empty((periods, replications), dtype=float)
        ids = np.arange(replications)
        for t in range(periods):
            uniforms[t] = (
                rng.permutation(ids) + rng.random()
            ) / replications

        probabilities = cdf_a + uniforms * (cdf_b - cdf_a)
        demands = demand_loc + demand_scale * ndtri(probabilities)

        states = np.full(
            (candidate_count, replications, n),
            initial_component,
            dtype=float,
        )
        values = np.zeros(candidate_count, dtype=float)

        target_array = targets[:, None]
        alpha_array = alphas[:, None]
        gain_array = gains[:, None]

        discount_factor = 1.0

        for t in range(periods):
            rounded = np.rint(states)

            # Estimate inventory that will expire before it can be useful.
            projected = rounded.copy()
            predicted_waste = np.zeros(
                (candidate_count, replications), dtype=float
            )

            for _ in range(n):
                predicted_waste += np.maximum(
                    projected[:, :, 0] - demand_mean, 0.0
                )

                spill = np.maximum(
                    demand_mean - projected[:, :, 0], 0.0
                )
                lower_bound = (
                    -max_backlog
                    - np.sum(projected[:, :, 2:m], axis=2)
                )
                new_first = np.maximum(
                    projected[:, :, 1] - spill, lower_bound
                )

                projected[:, :, :-1] = projected[:, :, 1:]
                projected[:, :, -1] = 0.0
                projected[:, :, 0] = new_first

            effective_position = (
                np.sum(rounded, axis=2)
                - alpha_array * predicted_waste
            )

            orders = np.clip(
                np.rint(
                    gain_array
                    * (target_array - effective_position)
                ),
                0,
                max_order,
            ).astype(np.int16)

            demand = demands[t][None, :]
            u = demand - np.sum(states[:, :, :m], axis=2)

            costs = (
                purchase_cost * orders
                + holding_cost
                * np.maximum(
                    0.0,
                    np.sum(states[:, :, 1:m], axis=2)
                    - np.maximum(
                        0.0, demand - states[:, :, 0]
                    ),
                )
                + backlog_cost * np.maximum(0.0, u)
                + disposal_cost
                * np.maximum(0.0, states[:, :, 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, u - max_backlog)
            )

            values += discount_factor * np.mean(costs, axis=1)

            spill = np.maximum(
                0.0, demand - states[:, :, 0]
            )
            lower_bound = (
                -max_backlog
                - np.sum(states[:, :, 2:m], axis=2)
            )
            new_first = np.maximum(
                states[:, :, 1] - spill, lower_bound
            )

            states[:, :, :-1] = states[:, :, 1:]
            states[:, :, -1] = orders
            states[:, :, 0] = new_first

            discount_factor *= discount

        return values

    protection_horizon = m + lead_time

    target_lower = -max_backlog - 8.0
    target_upper = min(
        protection_horizon * demand_high + 25.0,
        protection_horizon * demand_mean
        + 5.0 * demand_sd * math.sqrt(protection_horizon)
        + 25.0,
    )

    coarse_targets = np.arange(
        target_lower, target_upper + 2.5, 5.0
    )

    alpha_grid = (0.0, 0.5, 1.0, 1.5)
    gain_grid = (0.4, 0.65, 0.85, 1.0, 1.2)
    families = [
        (alpha, gain)
        for alpha in alpha_grid
        for gain in gain_grid
    ]

    broad_targets = np.tile(
        coarse_targets, len(families)
    )
    broad_alphas = np.repeat(
        [family[0] for family in families],
        coarse_targets.size,
    )
    broad_gains = np.repeat(
        [family[1] for family in families],
        coarse_targets.size,
    )

    broad_periods = min(horizon, 280)
    broad_values = simulate(
        broad_targets,
        broad_alphas,
        broad_gains,
        replications=36,
        periods=broad_periods,
        seed=1731,
    )

    family_values = np.empty(len(families), dtype=float)
    family_centers = np.empty(len(families), dtype=float)

    for j in range(len(families)):
        start = j * coarse_targets.size
        stop = start + coarse_targets.size
        local_values = broad_values[start:stop]
        local_best = int(np.argmin(local_values))

        family_values[j] = local_values[local_best]
        family_centers[j] = coarse_targets[local_best]

    selected_families = np.argsort(family_values)[:4]

    refined_targets = []
    refined_alphas = []
    refined_gains = []

    for family_index in selected_families:
        fine_targets = np.arange(
            family_centers[family_index] - 7.0,
            family_centers[family_index] + 7.01,
            0.5,
        )
        alpha, gain = families[family_index]

        refined_targets.extend(fine_targets)
        refined_alphas.extend([alpha] * fine_targets.size)
        refined_gains.extend([gain] * fine_targets.size)

    effective_periods = int(
        math.ceil(math.log(8e-4) / math.log(discount))
    )
    refined_periods = min(
        horizon, max(260, effective_periods), 710
    )

    refined_values = simulate(
        refined_targets,
        refined_alphas,
        refined_gains,
        replications=128,
        periods=refined_periods,
        seed=92821,
    )

    best = int(np.argmin(refined_values))
    target = float(refined_targets[best])
    alpha = float(refined_alphas[best])
    gain = float(refined_gains[best])

    def compute_order_amount(state):
        values = [float(value) for value in state]
        inventory_position = sum(values)
        predicted_waste = 0.0

        if alpha != 0.0:
            projected = values[:]

            for _ in range(n):
                if projected[0] > demand_mean:
                    predicted_waste += (
                        projected[0] - demand_mean
                    )

                spill = max(
                    0.0, demand_mean - projected[0]
                )
                lower_bound = (
                    -max_backlog
                    - sum(projected[2:m])
                )
                new_first = max(
                    projected[1] - spill, lower_bound
                )

                projected = (
                    [new_first]
                    + projected[2:]
                    + [0.0]
                )

        effective_position = (
            inventory_position - alpha * predicted_waste
        )
        order = int(
            np.rint(gain * (target - effective_position))
        )

        if order < 0:
            return 0
        if order > max_order:
            return max_order
        return order

    return compute_order_amount
