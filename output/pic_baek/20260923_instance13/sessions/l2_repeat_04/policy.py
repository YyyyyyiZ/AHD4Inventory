import math
import numpy as np

from scipy.optimize import differential_evolution
from scipy.stats import truncnorm


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    n = m + lead_time - 1

    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    horizon = int(params["horizon"])
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

    lower_z = (demand_low - parent_mean) / parent_std
    upper_z = (demand_high - parent_mean) / parent_std
    demand_distribution = truncnorm(
        lower_z,
        upper_z,
        loc=parent_mean,
        scale=parent_std,
    )

    truncated_mean = float(demand_distribution.mean())
    truncated_std = float(demand_distribution.std())

    # A table for E[(D-y)^+]. It is constructed from deterministic quantiles
    # to remain numerically stable even when the parent normal is far outside
    # the truncation interval.
    stop_grid_size = 500
    stop_grid = np.linspace(demand_low, demand_high, stop_grid_size + 1)
    quantile_count = 4096
    quantile_points = (np.arange(quantile_count) + 0.5) / quantile_count
    quantile_demands = demand_distribution.ppf(quantile_points)
    suffix_sums = np.empty(quantile_count + 1)
    suffix_sums[-1] = 0.0
    suffix_sums[:-1] = np.cumsum(quantile_demands[::-1])[::-1]

    stop_values = np.empty(stop_grid_size + 1)
    for i, y in enumerate(stop_grid):
        first = int(np.searchsorted(quantile_demands, y, side="right"))
        count = quantile_count - first
        stop_values[i] = (
            suffix_sums[first] - count * y
        ) / quantile_count

    # Terms below the simulation cutoff have negligible effect on selection.
    if 0.0 < discount < 1.0:
        effective_horizon = int(
            math.ceil(math.log(1.0e-7) / math.log(discount))
        )
        effective_horizon = max(effective_horizon, n + 5)
        simulation_horizon = min(horizon, effective_horizon)
    else:
        simulation_horizon = horizon

    def make_demands(number_of_paths, seed):
        rng = np.random.default_rng(seed)
        half = number_of_paths // 2
        uniforms = rng.random((half, simulation_horizon))
        uniforms = np.concatenate((uniforms, 1.0 - uniforms), axis=0)
        return demand_distribution.ppf(uniforms)

    training_demands = make_demands(40, 31751)
    validation_demands = make_demands(80, 90217)

    def evaluate(theta, policy_kind, demands):
        path_count = demands.shape[0]
        state = np.full((path_count, n), 5.0, dtype=float)
        value = 0.0
        weight = 1.0

        if policy_kind == 0:
            intercept, forecast_demand, gain, persistence = theta
        else:
            intercept, gain, persistence = theta

        for t in range(simulation_horizon):
            observed = np.rint(state)
            projected_shortage = np.zeros(path_count)

            if policy_kind == 0:
                # A Lindley recursion projects shortages through all inventory
                # and outstanding-order components.
                for j in range(n):
                    projected_shortage = np.maximum(
                        0.0,
                        persistence * projected_shortage
                        + forecast_demand
                        - observed[:, j],
                    )
            else:
                # Moment approximation to the stochastic shortage recursion.
                for j in range(n):
                    threshold = (
                        observed[:, j]
                        - persistence * projected_shortage
                    )
                    projected_shortage = np.interp(
                        threshold,
                        stop_grid,
                        stop_values,
                    )
                    below = threshold < demand_low
                    if np.any(below):
                        projected_shortage[below] = (
                            truncated_mean - threshold[below]
                        )

            raw_order = intercept + gain * projected_shortage
            order = np.clip(np.rint(raw_order), 0, max_order)

            demand = demands[:, t]
            age_inventory = state[:, :m]
            age_total = age_inventory.sum(axis=1)
            unmet_oldest = np.maximum(0.0, demand - state[:, 0])
            net_shortage = demand - age_total

            period_cost = (
                purchase_cost * order
                + holding_cost
                * np.maximum(
                    0.0,
                    age_inventory[:, 1:].sum(axis=1) - unmet_oldest,
                )
                + backlog_cost * np.maximum(0.0, net_shortage)
                + disposal_cost
                * np.maximum(0.0, state[:, 0] - demand)
                + lost_sales_cost
                * np.maximum(0.0, net_shortage - max_backlog)
            )
            value += weight * float(period_cost.mean())
            weight *= discount

            next_first = np.maximum(
                state[:, 1] - unmet_oldest,
                -max_backlog - state[:, 2:m].sum(axis=1),
            )
            state[:, :-1] = state[:, 1:]
            state[:, 0] = next_first
            state[:, -1] = order

        return value

    intercept_bound = float(min(max_order, 12))
    demand_lower_bound = max(
        demand_low,
        truncated_mean - 2.5 * truncated_std - 0.75,
    )
    demand_upper_bound = min(
        demand_high,
        truncated_mean + 1.5 * truncated_std + 0.75,
    )
    if demand_upper_bound <= demand_lower_bound + 1.0e-8:
        demand_lower_bound = demand_low
        demand_upper_bound = demand_high

    deterministic_bounds = [
        (-intercept_bound, intercept_bound),
        (demand_lower_bound, demand_upper_bound),
        (0.0, 2.5),
        (0.55, 1.18),
    ]
    expected_bounds = [
        (-intercept_bound, intercept_bound),
        (0.0, 2.5),
        (0.55, 1.18),
    ]

    candidate_policies = []

    try:
        deterministic_result = differential_evolution(
            lambda z: evaluate(z, 0, training_demands),
            deterministic_bounds,
            seed=2741,
            popsize=4,
            maxiter=7,
            tol=0.025,
            polish=False,
            updating="immediate",
            workers=1,
        )
        candidate_policies.append(
            (0, np.asarray(deterministic_result.x, dtype=float))
        )
        ranking = np.argsort(
            deterministic_result.population_energies
        )[:5]
        for index in ranking:
            candidate_policies.append(
                (
                    0,
                    np.asarray(
                        deterministic_result.population[index],
                        dtype=float,
                    ),
                )
            )

        best = np.asarray(deterministic_result.x, dtype=float)
        for change in (-0.5, 0.5):
            altered = best.copy()
            altered[0] += change
            candidate_policies.append((0, altered))
        for change in (-0.2, 0.2):
            altered = best.copy()
            altered[1] = np.clip(
                altered[1] + change,
                demand_low,
                demand_high,
            )
            candidate_policies.append((0, altered))
    except Exception:
        pass

    try:
        expected_result = differential_evolution(
            lambda z: evaluate(z, 1, training_demands),
            expected_bounds,
            seed=9187,
            popsize=4,
            maxiter=7,
            tol=0.025,
            polish=False,
            updating="immediate",
            workers=1,
        )
        candidate_policies.append(
            (1, np.asarray(expected_result.x, dtype=float))
        )
        ranking = np.argsort(expected_result.population_energies)[:5]
        for index in ranking:
            candidate_policies.append(
                (
                    1,
                    np.asarray(
                        expected_result.population[index],
                        dtype=float,
                    ),
                )
            )

        best = np.asarray(expected_result.x, dtype=float)
        for change in (-0.5, 0.5):
            altered = best.copy()
            altered[0] += change
            candidate_policies.append((1, altered))
        for change in (-0.1, 0.1):
            altered = best.copy()
            altered[1] = max(0.0, altered[1] + change)
            candidate_policies.append((1, altered))
    except Exception:
        pass

    # Robust fallback and benchmark policies.
    candidate_policies.extend(
        [
            (
                0,
                np.array(
                    [0.0, truncated_mean, 1.0, 1.0],
                    dtype=float,
                ),
            ),
            (
                0,
                np.array(
                    [-0.5 * truncated_mean, truncated_mean, 1.0, 1.0],
                    dtype=float,
                ),
            ),
            (
                0,
                np.array(
                    [truncated_mean, 0.0, 0.0, 1.0],
                    dtype=float,
                ),
            ),
            (
                0,
                np.array([-1.0, 0.0, 0.0, 1.0], dtype=float),
            ),
            (
                1,
                np.array([0.0, 1.0, 1.0], dtype=float),
            ),
            (
                1,
                np.array(
                    [-0.5 * truncated_mean, 1.0, 1.0],
                    dtype=float,
                ),
            ),
        ]
    )

    best_kind = 0
    best_theta = np.array(
        [0.0, truncated_mean, 1.0, 1.0],
        dtype=float,
    )
    best_score = float("inf")

    for kind, theta in candidate_policies:
        try:
            score = evaluate(theta, kind, validation_demands)
        except Exception:
            continue
        if np.isfinite(score) and score < best_score:
            best_score = score
            best_kind = kind
            best_theta = np.asarray(theta, dtype=float).copy()

    if best_kind == 0:
        intercept = float(best_theta[0])
        forecast_demand = float(best_theta[1])
        gain = float(best_theta[2])
        persistence = float(best_theta[3])

        def compute_order_amount(state):
            shortage = 0.0
            for component in state:
                shortage = max(
                    0.0,
                    persistence * shortage
                    + forecast_demand
                    - float(component),
                )
            order = int(np.rint(intercept + gain * shortage))
            if order < 0:
                return 0
            if order > max_order:
                return max_order
            return order

    else:
        intercept = float(best_theta[0])
        gain = float(best_theta[1])
        persistence = float(best_theta[2])
        grid_scale = stop_grid_size / (
            demand_high - demand_low
        )

        def scalar_stop_loss(threshold):
            if threshold <= demand_low:
                return truncated_mean - threshold
            if threshold >= demand_high:
                return 0.0

            position = (threshold - demand_low) * grid_scale
            index = int(position)
            fraction = position - index
            return float(
                stop_values[index]
                + fraction
                * (stop_values[index + 1] - stop_values[index])
            )

        def compute_order_amount(state):
            shortage = 0.0
            for component in state:
                threshold = (
                    float(component) - persistence * shortage
                )
                shortage = scalar_stop_loss(threshold)

            order = int(np.rint(intercept + gain * shortage))
            if order < 0:
                return 0
            if order > max_order:
                return max_order
            return order

    return compute_order_amount
