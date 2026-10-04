import math
import numpy as np
from scipy.stats import truncnorm, qmc


def _generate_demands(params, sample_count, periods, seed):
    mean = float(params["demand_mean"])
    std = float(params["demand_std"])
    low = float(params["demand_low"])
    high = float(params["demand_high"])

    sampler = qmc.Sobol(d=periods, scramble=True, seed=seed)
    uniforms = sampler.random_base2(int(round(math.log2(sample_count))))
    a = (low - mean) / std
    b = (high - mean) / std
    return truncnorm.ppf(uniforms, a, b, loc=mean, scale=std)


def _evaluate_candidates(params, candidates, sample_count, periods, seed):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    state_length = m + lead_time - 1
    max_backlog = float(params["max_backlog"])
    max_order = int(params["max_order"])
    discount = float(params["discount"])

    targets = np.asarray([c[0] for c in candidates], dtype=float)
    forecasts = np.asarray([c[1] for c in candidates], dtype=float)
    waste_weights = np.asarray([c[2] for c in candidates], dtype=float)

    candidate_count = len(candidates)
    demands = _generate_demands(
        params, sample_count, periods, seed
    )

    states = np.full(
        (candidate_count, sample_count, state_length),
        float(params["initial_component"]),
        dtype=float,
    )
    values = np.zeros(candidate_count, dtype=float)

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    forecast_matrix = forecasts[:, None]
    nonzero_waste = np.nonzero(waste_weights != 0.0)[0]
    discount_factor = 1.0

    for t in range(periods):
        # Project the rounded observed state to the arrival time of a new order.
        projected = np.rint(states).copy()
        for _ in range(lead_time):
            first = np.maximum(
                projected[:, :, 1]
                - np.maximum(0.0, forecast_matrix - projected[:, :, 0]),
                -max_backlog
                - np.sum(projected[:, :, 2:m], axis=2),
            )
            projected[:, :, :-1] = projected[:, :, 1:]
            projected[:, :, 0] = first
            projected[:, :, -1] = 0.0

        effective_inventory = np.sum(projected[:, :, :m], axis=2)

        # Optionally remove inventory forecast to expire before use.
        if nonzero_waste.size:
            waste_state = projected[nonzero_waste].copy()
            waste_forecast = forecasts[nonzero_waste, None]
            predicted_waste = np.zeros(
                (nonzero_waste.size, sample_count), dtype=float
            )

            for _ in range(m):
                predicted_waste += np.maximum(
                    0.0, waste_state[:, :, 0] - waste_forecast
                )
                first = np.maximum(
                    waste_state[:, :, 1]
                    - np.maximum(
                        0.0, waste_forecast - waste_state[:, :, 0]
                    ),
                    -max_backlog
                    - np.sum(waste_state[:, :, 2:m], axis=2),
                )
                waste_state[:, :, :-1] = waste_state[:, :, 1:]
                waste_state[:, :, 0] = first
                waste_state[:, :, -1] = 0.0

            effective_inventory[nonzero_waste] -= (
                waste_weights[nonzero_waste, None] * predicted_waste
            )

        orders = np.floor(
            targets[:, None] - effective_inventory + 0.5
        )
        orders = np.clip(orders, 0, max_order)

        demand = demands[:, t][None, :]
        total_inventory = np.sum(states[:, :, :m], axis=2)
        unmet = demand - total_inventory

        holding = np.maximum(
            0.0,
            np.sum(states[:, :, 1:m], axis=2)
            - np.maximum(0.0, demand - states[:, :, 0]),
        )

        costs = (
            purchase_cost * orders
            + holding_cost * holding
            + backlog_cost * np.maximum(0.0, unmet)
            + disposal_cost
            * np.maximum(0.0, states[:, :, 0] - demand)
            + lost_sales_cost
            * np.maximum(0.0, unmet - max_backlog)
        )
        values += discount_factor * np.mean(costs, axis=1)
        discount_factor *= discount

        first = np.maximum(
            states[:, :, 1]
            - np.maximum(0.0, demand - states[:, :, 0]),
            -max_backlog - np.sum(states[:, :, 2:m], axis=2),
        )
        states[:, :, :-1] = states[:, :, 1:]
        states[:, :, 0] = first
        states[:, :, -1] = orders

    return values


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    discount = float(params["discount"])
    horizon = int(params["horizon"])

    parent_mean = float(params["demand_mean"])
    parent_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])

    a = (demand_low - parent_mean) / parent_std
    b = (demand_high - parent_mean) / parent_std
    truncated_mean = float(
        truncnorm.mean(
            a, b, loc=parent_mean, scale=parent_std
        )
    )
    truncated_std = float(
        truncnorm.std(
            a, b, loc=parent_mean, scale=parent_std
        )
    )

    # The omitted discounted tail has at most roughly 0.15% of the
    # infinite-horizon weight.
    tuning_periods = min(
        horizon,
        int(math.ceil(math.log(1.5e-3) / math.log(discount))),
    )

    target_low = -max_backlog
    target_high = demand_high * m + max_backlog

    broad_targets = list(
        np.arange(target_low, target_high + 1e-10, 4.0)
    )
    if target_high - broad_targets[-1] > 1e-8:
        broad_targets.append(target_high)

    broad_forecasts = np.clip(
        truncated_mean
        + truncated_std * np.asarray([-1.0, 0.0, 1.0]),
        demand_low,
        demand_high,
    )

    broad_candidates = [
        (float(target), float(forecast), float(waste_weight))
        for waste_weight in (0.0, 1.0)
        for forecast in broad_forecasts
        for target in broad_targets
    ]

    broad_values = _evaluate_candidates(
        params,
        broad_candidates,
        sample_count=64,
        periods=tuning_periods,
        seed=12973,
    )
    broad_best = broad_candidates[int(np.argmin(broad_values))]
    broad_target, broad_forecast, broad_waste_weight = broad_best

    fine_targets = np.unique(
        np.clip(
            broad_target + np.arange(-3.5, 3.5001, 0.5),
            target_low,
            target_high,
        )
    )
    fine_forecasts = np.unique(
        np.clip(
            broad_forecast
            + truncated_std * np.linspace(-0.5, 0.5, 5),
            demand_low,
            demand_high,
        )
    )
    if broad_waste_weight < 0.5:
        fine_waste_weights = (0.0, 0.5)
    else:
        fine_waste_weights = (0.5, 1.0)

    fine_candidates = [
        (float(target), float(forecast), float(waste_weight))
        for waste_weight in fine_waste_weights
        for forecast in fine_forecasts
        for target in fine_targets
    ]

    fine_values = _evaluate_candidates(
        params,
        fine_candidates,
        sample_count=128,
        periods=tuning_periods,
        seed=84017,
    )

    finalist_indices = np.argsort(fine_values)[
        : min(12, len(fine_candidates))
    ]
    finalists = [
        fine_candidates[int(index)] for index in finalist_indices
    ]

    validation_values = _evaluate_candidates(
        params,
        finalists,
        sample_count=256,
        periods=tuning_periods,
        seed=318491,
    )
    target, forecast, waste_weight = finalists[
        int(np.argmin(validation_values))
    ]

    def compute_order_amount(state):
        projected = [float(value) for value in state]

        for _ in range(lead_time):
            first = max(
                projected[1]
                - max(0.0, forecast - projected[0]),
                -max_backlog - sum(projected[2:m]),
            )
            projected = [first] + projected[2:] + [0.0]

        effective_inventory = sum(projected[:m])

        if waste_weight != 0.0:
            waste_state = projected
            predicted_waste = 0.0

            for _ in range(m):
                predicted_waste += max(
                    0.0, waste_state[0] - forecast
                )
                first = max(
                    waste_state[1]
                    - max(0.0, forecast - waste_state[0]),
                    -max_backlog - sum(waste_state[2:m]),
                )
                waste_state = [first] + waste_state[2:] + [0.0]

            effective_inventory -= waste_weight * predicted_waste

        order = math.floor(target - effective_inventory + 0.5)
        if order <= 0:
            return 0
        if order >= max_order:
            return max_order
        return int(order)

    return compute_order_amount
