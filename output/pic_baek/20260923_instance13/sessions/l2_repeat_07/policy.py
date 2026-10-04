import numpy as np
from scipy.special import ndtr, ndtri
from scipy.optimize import differential_evolution


def _sample_truncated_normal(mu, sigma, low, high, periods, paths, seed):
    rng = np.random.default_rng(seed)

    # Antithetic samples reduce noise in the policy search.
    half = (paths + 1) // 2
    u = rng.random((periods, half))
    u = np.concatenate((u, 1.0 - u), axis=1)[:, :paths]

    a = (low - mu) / sigma
    b = (high - mu) / sigma
    cdf_a = ndtr(a)
    width = ndtr(b) - cdf_a
    return mu + sigma * ndtri(cdf_a + width * u)


def design(params):
    m = int(params["lifetime"])
    lead_time = int(params["lead_time"])
    state_length = m + lead_time - 1

    max_order = int(params["max_order"])
    max_backlog = float(params["max_backlog"])
    discount = float(params["discount"])
    horizon = int(params["horizon"])

    purchase_cost = float(params["purchase_cost"])
    holding_cost = float(params["holding_cost"])
    backlog_cost = float(params["backlog_cost"])
    disposal_cost = float(params["disposal_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])

    demand_mean = float(params["demand_mean"])
    demand_std = float(params["demand_std"])
    demand_low = float(params["demand_low"])
    demand_high = float(params["demand_high"])
    initial_component = float(params["initial_component"])

    optimization_periods = min(horizon, 260)
    tail_window = min(60, optimization_periods)

    def make_objective(paths, seed, record=False):
        demands = _sample_truncated_normal(
            demand_mean,
            demand_std,
            demand_low,
            demand_high,
            optimization_periods,
            paths,
            seed,
        )
        discounts = discount ** np.arange(optimization_periods)

        if discount == 1.0:
            tail_multiplier = float(horizon - optimization_periods)
        else:
            tail_multiplier = (
                discount ** optimization_periods - discount ** horizon
            ) / (1.0 - discount)

        history = []

        def objective(coefficients):
            intercept, oldest_weight, inventory_weight, pipeline_weight = coefficients

            state = np.full(
                (paths, state_length), initial_component, dtype=float
            )
            value = 0.0
            recent_cost = 0.0

            for t in range(optimization_periods):
                rounded = np.rint(state)

                score = (
                    intercept
                    - oldest_weight * rounded[:, 0]
                    - inventory_weight * np.sum(rounded[:, 1:m], axis=1)
                    - pipeline_weight * np.sum(rounded[:, m:], axis=1)
                )
                order = np.clip(np.rint(score), 0, max_order)

                demand = demands[t]
                residual_after_oldest = np.maximum(
                    0.0, demand - state[:, 0]
                )
                shortage = demand - np.sum(state[:, :m], axis=1)

                period_cost = (
                    purchase_cost * order
                    + holding_cost
                    * np.maximum(
                        0.0,
                        np.sum(state[:, 1:m], axis=1)
                        - residual_after_oldest,
                    )
                    + backlog_cost * np.maximum(0.0, shortage)
                    + disposal_cost * np.maximum(0.0, state[:, 0] - demand)
                    + lost_sales_cost
                    * np.maximum(0.0, shortage - max_backlog)
                )

                mean_cost = float(np.mean(period_cost))
                value += discounts[t] * mean_cost

                if t >= optimization_periods - tail_window:
                    recent_cost += mean_cost / tail_window

                new_first = np.maximum(
                    state[:, 1] - residual_after_oldest,
                    -max_backlog - np.sum(state[:, 2:m], axis=1),
                )

                state[:, :-1] = state[:, 1:]
                state[:, 0] = new_first
                state[:, -1] = order

            # By this point the simulated system is effectively stationary.
            value += tail_multiplier * recent_cost

            if record:
                history.append(
                    (value, np.asarray(coefficients, dtype=float).copy())
                )
            return value

        return objective, history, demands

    training_objective, history, training_demands = make_objective(
        paths=512, seed=192837, record=True
    )

    conditional_demand_mean = float(np.mean(training_demands))
    target_scale = conditional_demand_mean * state_length
    target_limit = 12.0 * state_length + max_order
    intercept_limit = 4.0 * target_limit

    population = []

    # Ordinary order-up-to policies.
    for target in np.linspace(0.0, target_limit, 17):
        population.append([target, 1.0, 1.0, 1.0])

    # Constant-order policies, including the no-order policy.
    for order in np.linspace(0.0, max_order, 8):
        population.append([order, 0.0, 0.0, 0.0])

    # Different feedback gains around a demand-based target.
    for gain in (0.4, 0.7, 1.0, 1.5, 2.2, 3.2):
        population.append(
            [gain * target_scale, gain, gain, gain]
        )

    rng = np.random.default_rng(918273)
    while len(population) < 44:
        weights = rng.uniform(0.05, 3.5, 3)
        target = rng.uniform(0.0, target_limit)
        intercept = min(
            intercept_limit, float(np.mean(weights) * target)
        )
        population.append(
            [intercept, weights[0], weights[1], weights[2]]
        )

    population = np.asarray(population, dtype=float)
    bounds = [
        (-10.0, intercept_limit),
        (0.0, 4.0),
        (0.0, 4.0),
        (0.0, 4.0),
    ]

    try:
        result = differential_evolution(
            training_objective,
            bounds,
            init=population,
            maxiter=15,
            tol=0.003,
            polish=False,
            seed=7361,
            updating="immediate",
            workers=1,
        )
        initial_best = np.asarray(result.x, dtype=float)
    except Exception:
        initial_best = np.array(
            [target_scale, 1.0, 1.0, 1.0], dtype=float
        )

    validation_objective, _, _ = make_objective(
        paths=1024, seed=817263, record=False
    )

    def clipped(coefficients):
        result = np.asarray(coefficients, dtype=float).copy()
        result[0] = np.clip(result[0], -10.0, intercept_limit)
        result[1:] = np.clip(result[1:], 0.0, 4.0)
        return result

    candidates = [initial_best]

    # Reconsider several distinct good policies on independent scenarios.
    diversity_scale = np.array(
        [max(20.0, target_scale, target_limit / 2.0), 1.0, 1.0, 1.0]
    )
    for _, candidate in sorted(history, key=lambda item: item[0]):
        if all(
            np.linalg.norm(
                (candidate - existing) / diversity_scale
            ) > 0.025
            for existing in candidates
        ):
            candidates.append(candidate)
            if len(candidates) >= 13:
                break

    for delta in (-4.0, -2.0, -1.0, -0.5, 0.5, 1.0, 2.0, 4.0):
        candidates.append(
            clipped(initial_best + np.array([delta, 0.0, 0.0, 0.0]))
        )

    for index in range(1, 4):
        for delta in (-0.35, -0.15, 0.15, 0.35):
            candidate = initial_best.copy()
            candidate[index] += delta
            candidates.append(clipped(candidate))

    for factor in (0.75, 0.88, 1.12, 1.30):
        candidates.append(clipped(initial_best * factor))

    validation_values = [
        validation_objective(candidate) for candidate in candidates
    ]
    best = candidates[int(np.argmin(validation_values))]

    # A small final coordinate refinement.
    refined = [best]

    for delta in (-1.5, -0.75, -0.25, 0.25, 0.75, 1.5):
        refined.append(
            clipped(best + np.array([delta, 0.0, 0.0, 0.0]))
        )

    for index in range(1, 4):
        for delta in (-0.12, 0.12):
            candidate = best.copy()
            candidate[index] += delta
            refined.append(clipped(candidate))

    for factor in (0.92, 1.08):
        refined.append(clipped(best * factor))

    refined_values = [
        validation_objective(candidate) for candidate in refined
    ]
    best = refined[int(np.argmin(refined_values))]

    intercept = float(best[0])
    oldest_weight = float(best[1])
    inventory_weight = float(best[2])
    pipeline_weight = float(best[3])

    def compute_order_amount(state):
        score = (
            intercept
            - oldest_weight * float(state[0])
            - inventory_weight * sum(state[1:m])
            - pipeline_weight * sum(state[m:])
        )
        order = int(np.rint(score))
        if order < 0:
            return 0
        if order > max_order:
            return max_order
        return order

    return compute_order_amount
