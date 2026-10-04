import math
import numpy as np
from scipy.stats import truncnorm


def _demand_paths(mu, sigma, low, high, count, horizon, seed):
    """Latin-hypercube demand paths for low-variance policy selection."""
    a = (low - mu) / sigma
    b = (high - mu) / sigma

    rng = np.random.default_rng(seed)
    strata = (np.arange(count, dtype=float) + 0.5) / count
    uniforms = np.empty((count, horizon), dtype=float)

    for t in range(horizon):
        uniforms[:, t] = strata[rng.permutation(count)]

    return truncnorm.ppf(
        uniforms, a, b, loc=mu, scale=sigma
    )


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    state_length = m + lead_time - 1

    discount = float(params["discount"])
    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    parent_mean = float(params["demand_mean"])
    parent_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])
    initial_component = float(params["initial_component"])
    horizon = int(params["horizon"])

    a = (demand_low - parent_mean) / parent_std
    b = (demand_high - parent_mean) / parent_std
    demand_mean = float(
        truncnorm.mean(a, b, loc=parent_mean, scale=parent_std)
    )
    demand_std = float(
        truncnorm.std(a, b, loc=parent_mean, scale=parent_std)
    )

    def evaluate_candidates(candidates, path_count, sim_horizon, seed):
        candidate_count = len(candidates)

        targets = np.asarray(
            [candidate[0] for candidate in candidates], dtype=float
        )[:, None]
        projection_demands = np.asarray(
            [candidate[1] for candidate in candidates], dtype=float
        )[:, None]
        gains = np.asarray(
            [candidate[2] for candidate in candidates], dtype=float
        )[:, None]

        demands = _demand_paths(
            parent_mean,
            parent_std,
            demand_low,
            demand_high,
            path_count,
            sim_horizon,
            seed,
        )

        states = np.full(
            (candidate_count, path_count, state_length),
            initial_component,
            dtype=float,
        )
        values = np.zeros(candidate_count, dtype=float)
        discount_factor = 1.0

        for t in range(sim_horizon):
            # Project the observed state to the time at which the current
            # order would arrive. Future orders are zero in this projection.
            projected = np.rint(states)

            for _ in range(lead_time):
                projected_first = np.maximum(
                    projected[:, :, 1]
                    - np.maximum(
                        0.0,
                        projection_demands - projected[:, :, 0],
                    ),
                    -max_backlog
                    - np.sum(projected[:, :, 2:m], axis=2),
                )

                projected[:, :, :-1] = projected[:, :, 1:].copy()
                projected[:, :, -1] = 0.0
                projected[:, :, 0] = projected_first

            projected_inventory = np.sum(
                projected[:, :, :m], axis=2
            )

            raw_orders = demand_mean + gains * (
                targets - projected_inventory - demand_mean
            )
            orders = np.clip(
                np.floor(raw_orders + 1.0e-10),
                0,
                max_order,
            )

            demand = demands[:, t][None, :]
            inventory_total = np.sum(states[:, :, :m], axis=2)
            shortage = demand - inventory_total

            held = np.maximum(
                0.0,
                np.sum(states[:, :, 1:m], axis=2)
                - np.maximum(0.0, demand - states[:, :, 0]),
            )

            costs = (
                purchase_cost * orders
                + holding_cost * held
                + backlog_cost * np.maximum(0.0, shortage)
                + disposal_cost
                * np.maximum(0.0, states[:, :, 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, shortage - max_backlog)
            )

            values += discount_factor * np.mean(costs, axis=1)

            next_first = np.maximum(
                states[:, :, 1]
                - np.maximum(0.0, demand - states[:, :, 0]),
                -max_backlog
                - np.sum(states[:, :, 2:m], axis=2),
            )

            states[:, :, :-1] = states[:, :, 1:].copy()
            states[:, :, -1] = orders
            states[:, :, 0] = next_first

            discount_factor *= discount

        return values

    # Coarse search over projected-inventory targets, projection-demand
    # corrections, and feedback gains.
    gains = (0.25, 0.50, 0.75, 1.00, 1.25)
    projection_grid = np.unique(
        np.clip(
            demand_mean
            + demand_std * np.asarray((-0.9, 0.0, 0.9)),
            demand_low,
            demand_high,
        )
    )

    broad_candidates = []
    target_upper = demand_high * m

    for gain in gains:
        # The extended lower bound lets low-gain candidates represent a
        # deliberate no-order policy at the backlog boundary.
        target_lower = min(
            -max_backlog,
            -max_backlog + demand_mean - demand_mean / gain,
        )
        target_grid = np.arange(
            target_lower,
            target_upper + 1.500001,
            3.0,
        )

        for projection_demand in projection_grid:
            for target in target_grid:
                broad_candidates.append(
                    (
                        float(target),
                        float(projection_demand),
                        float(gain),
                    )
                )

    broad_values = evaluate_candidates(
        broad_candidates,
        path_count=64,
        sim_horizon=min(horizon, 400),
        seed=173,
    )

    # Preserve the best basin for every coarse projection-demand value.
    basin_centers = []
    for projection_demand in projection_grid:
        indices = [
            i
            for i, candidate in enumerate(broad_candidates)
            if candidate[1] == projection_demand
        ]
        local_index = indices[
            int(np.argmin(broad_values[indices]))
        ]
        basin_centers.append(broad_candidates[local_index])

    middle_candidates = []
    for base_target, base_projection, base_gain in basin_centers:
        for target_offset in (-2.0, -1.0, 0.0, 1.0, 2.0):
            for projection_offset in (-0.3, 0.0, 0.3):
                for gain_offset in (-0.15, 0.0, 0.15):
                    middle_candidates.append(
                        (
                            base_target + target_offset,
                            float(
                                np.clip(
                                    base_projection
                                    + projection_offset * demand_std,
                                    demand_low,
                                    demand_high,
                                )
                            ),
                            float(
                                np.clip(
                                    base_gain + gain_offset,
                                    0.15,
                                    1.5,
                                )
                            ),
                        )
                    )

    middle_values = evaluate_candidates(
        middle_candidates,
        path_count=128,
        sim_horizon=min(horizon, 700),
        seed=941,
    )
    middle_best = middle_candidates[int(np.argmin(middle_values))]

    # Final local search using the full objective horizon.
    fine_candidates = []
    for target_offset in np.arange(-1.0, 1.0001, 0.25):
        for projection_offset in (-0.15, 0.0, 0.15):
            for gain_offset in (-0.075, 0.0, 0.075):
                fine_candidates.append(
                    (
                        middle_best[0] + float(target_offset),
                        float(
                            np.clip(
                                middle_best[1]
                                + projection_offset * demand_std,
                                demand_low,
                                demand_high,
                            )
                        ),
                        float(
                            np.clip(
                                middle_best[2] + gain_offset,
                                0.1,
                                1.6,
                            )
                        ),
                    )
                )

    fine_values = evaluate_candidates(
        fine_candidates,
        path_count=256,
        sim_horizon=horizon,
        seed=2357,
    )

    target, projection_demand, gain = fine_candidates[
        int(np.argmin(fine_values))
    ]

    def compute_order_amount(state):
        projected = [float(value) for value in state]

        # Project to the arrival epoch of the order being selected now.
        for _ in range(lead_time):
            projected_first = max(
                projected[1]
                - max(0.0, projection_demand - projected[0]),
                -max_backlog - sum(projected[2:m]),
            )
            projected = projected[1:] + [0.0]
            projected[0] = projected_first

        projected_inventory = sum(projected[:m])
        raw_order = demand_mean + gain * (
            target - projected_inventory - demand_mean
        )

        if raw_order <= 0.0:
            return 0
        if raw_order >= max_order:
            return max_order
        return int(math.floor(raw_order + 1.0e-10))

    return compute_order_amount
