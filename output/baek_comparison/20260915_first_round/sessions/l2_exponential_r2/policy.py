def design(params):
    import math
    import numpy as np
    from scipy.optimize import differential_evolution, minimize, minimize_scalar
    from scipy.stats import qmc

    lead_time = int(params["lead_time"])
    mean_demand = float(params["mean_demand"])
    holding_cost = float(params["holding_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    horizon = int(params.get("horizon", 50))

    # Deterministic low-discrepancy demand paths used only during initialization.
    sample_power = 12
    sample_count = 1 << sample_power
    cost_ratio = lost_sales_cost / max(holding_cost, 1e-12)
    seed = 24681357 + 101 * lead_time + int(round(1000.0 * cost_ratio))

    uniforms = qmc.Sobol(
        d=horizon, scramble=True, seed=seed
    ).random_base2(sample_power)
    sampled_demands = np.rint(
        -mean_demand * np.log1p(-uniforms)
    ).T

    a_bounds = (0.35 * mean_demand, 2.8 * mean_demand)
    c_bounds = (0.30, 1.40)
    g_bounds = (0.65, 1.55)
    bounds = [a_bounds, c_bounds, g_bounds]

    def simulated_cost(theta):
        intercept, residual_weight, scale_multiplier = map(float, theta)
        effective_scale = mean_demand * scale_multiplier

        rounded_mean = (
            np.exp(-0.5 / effective_scale)
            / (-np.expm1(-1.0 / effective_scale))
        )

        inventory = np.zeros(sample_count, dtype=float)
        pipeline = np.zeros((lead_time, sample_count), dtype=float)
        total_cost = 0.0

        def expected_leftover(values):
            n = np.maximum(np.ceil(values) - 1.0, 0.0)
            tail = np.exp(-(n + 0.5) / effective_scale)
            result = (
                values * (1.0 - tail)
                - rounded_mean * (-np.expm1(-n / effective_scale))
                + n * tail
            )
            return np.maximum(result, 0.0)

        for period in range(lead_time + horizon):
            inventory += pipeline[0]
            outstanding = pipeline[1:]

            projected = expected_leftover(inventory)
            for arrival in outstanding:
                projected = expected_leftover(projected + arrival)

            order = np.maximum(
                0.0, intercept - residual_weight * projected
            )

            pipeline[:-1] = outstanding
            pipeline[-1] = order

            if period >= lead_time:
                demand = sampled_demands[period - lead_time]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                total_cost += (
                    holding_cost * inventory.mean()
                    + lost_sales_cost * (demand - sales).mean()
                )

        return float(total_cost)

    base_intercept = mean_demand * (
        0.35 + 0.58 * math.log1p(cost_ratio)
    )
    base_intercept = min(
        max(base_intercept, a_bounds[0]), a_bounds[1]
    )

    rng = np.random.default_rng(seed + 7919)
    initial_population = np.column_stack(
        (
            rng.uniform(*a_bounds, 18),
            rng.uniform(*c_bounds, 18),
            rng.uniform(*g_bounds, 18),
        )
    )

    presets = np.array(
        [
            [base_intercept, 0.80, 1.05],
            [base_intercept, 1.00, 1.00],
            [0.85 * base_intercept, 0.65, 1.00],
            [1.15 * base_intercept, 1.00, 1.15],
            [0.85 * mean_demand, 0.50, 0.85],
            [1.80 * mean_demand, 0.80, 1.20],
        ],
        dtype=float,
    )
    presets[:, 0] = np.clip(presets[:, 0], *a_bounds)
    initial_population[: len(presets)] = presets

    result = differential_evolution(
        simulated_cost,
        bounds,
        init=initial_population,
        maxiter=10,
        tol=1e-5,
        atol=0.0,
        polish=False,
        seed=seed + 17,
        updating="immediate",
        workers=1,
    )

    candidates = [(np.asarray(result.x, dtype=float), float(result.fun))]

    try:
        polished = minimize(
            simulated_cost,
            result.x,
            method="Powell",
            bounds=bounds,
            options={
                "maxiter": 2,
                "xtol": 0.002,
                "ftol": 1e-5,
            },
        )
        if np.all(np.isfinite(polished.x)) and math.isfinite(polished.fun):
            candidates.append(
                (np.asarray(polished.x, dtype=float), float(polished.fun))
            )
    except Exception:
        pass

    # Include a robust standard projected-inventory policy as a fallback.
    try:
        standard = minimize_scalar(
            lambda intercept: simulated_cost((intercept, 1.0, 1.0)),
            bounds=a_bounds,
            method="bounded",
            options={"xatol": max(0.05, 0.001 * mean_demand)},
        )
        if math.isfinite(standard.fun):
            candidates.append(
                (
                    np.array([standard.x, 1.0, 1.0], dtype=float),
                    float(standard.fun),
                )
            )
    except Exception:
        pass

    best_theta, _ = min(candidates, key=lambda item: item[1])
    intercept, residual_weight, scale_multiplier = map(float, best_theta)

    effective_scale = mean_demand * scale_multiplier
    rounded_effective_mean = (
        math.exp(-0.5 / effective_scale)
        / (-math.expm1(-1.0 / effective_scale))
    )
    large_inventory_cutoff = 50.0 * effective_scale + 1.0

    def one_period_expected_leftover(value):
        value = float(value)
        if value <= 0.0:
            return 0.0
        if not math.isfinite(value):
            return value
        if value > large_inventory_cutoff:
            return max(0.0, value - rounded_effective_mean)

        n = math.ceil(value) - 1
        tail = math.exp(-(n + 0.5) / effective_scale)
        result = (
            value * (1.0 - tail)
            - rounded_effective_mean
            * (-math.expm1(-n / effective_scale))
            + n * tail
        )
        return max(0.0, result)

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        projected = one_period_expected_leftover(
            float(on_hand_inventory)
        )
        for arrival in pipeline_orders:
            projected = one_period_expected_leftover(
                projected + float(arrival)
            )

        order = intercept - residual_weight * projected
        if not math.isfinite(order):
            return 0.0 if order < 0.0 else float(intercept)
        return float(max(0.0, order))

    return compute_order_amount
