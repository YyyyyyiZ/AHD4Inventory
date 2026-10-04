def design(params):
    import math
    import numpy as np
    from scipy.optimize import differential_evolution, minimize
    from scipy.stats import qmc

    L = int(params["lead_time"])
    mean_demand = float(params["mean_demand"])
    holding_cost = float(params["holding_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    horizon = int(params["horizon"])

    cost_ratio = lost_sales_cost / holding_cost
    normalized_p = min(10.0, max(2.0, cost_ratio))

    # Exact mean of the rounded exponential demand.
    rounded_mean = (
        math.exp(-0.5 / mean_demand)
        / (-math.expm1(-1.0 / mean_demand))
    )

    def demand_sample(power, seed):
        uniforms = qmc.Sobol(
            d=horizon, scramble=True, seed=seed
        ).random_base2(power)
        return np.rint(-mean_demand * np.log1p(-uniforms))

    train_demands = demand_sample(12, 910 + L)
    validation_demands = demand_sample(11, 1910 + L)

    def simulate_curve(z, demands):
        if L == 2:
            intercept = z[0] * mean_demand
            inventory_weight = z[1]
            weights = np.array([z[2]], dtype=float)
            order_cap = z[3] * mean_demand
        else:
            positions = np.linspace(0.0, 1.0, L - 1)
            intercept = z[0] * mean_demand
            inventory_weight = z[1]
            weights = z[2] * np.exp(
                z[3] * positions + z[4] * positions * (1.0 - positions)
            )
            order_cap = z[5] * mean_demand

        n = demands.shape[0]
        inventory = np.zeros(n)
        pipeline = np.zeros((n, L - 1))
        total_cost = 0.0

        for t in range(L + horizon):
            orders = np.clip(
                intercept
                - inventory_weight * inventory
                - pipeline @ weights,
                0.0,
                order_cap,
            )

            if t >= L:
                demand = demands[:, t - L]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                total_cost += np.mean(
                    inventory + cost_ratio * (demand - sales)
                )

            inventory += pipeline[:, 0]
            pipeline[:, :-1] = pipeline[:, 1:]
            pipeline[:, -1] = orders

        return float(total_cost)

    def simulate_capped_base_stock(y, demands):
        target = y[0] * mean_demand
        cap = y[1] * mean_demand
        n = demands.shape[0]
        inventory = np.zeros(n)
        pipeline = np.zeros((n, L - 1))
        total_cost = 0.0

        for t in range(L + horizon):
            orders = np.minimum(
                cap,
                np.maximum(
                    target - inventory - pipeline.sum(axis=1), 0.0
                ),
            )

            if t >= L:
                demand = demands[:, t - L]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                total_cost += np.mean(
                    inventory + cost_ratio * (demand - sales)
                )

            inventory += pipeline[:, 0]
            pipeline[:, :-1] = pipeline[:, 1:]
            pipeline[:, -1] = orders

        return float(total_cost)

    cbs_result = differential_evolution(
        lambda y: simulate_capped_base_stock(y, train_demands),
        bounds=[(0.0, L + 5.0), (0.25, 2.5)],
        popsize=5,
        maxiter=10,
        tol=0.002,
        polish=False,
        seed=33 + L,
        workers=1,
        updating="immediate",
    )
    base_stock_target, base_cap = cbs_result.x

    if L == 2:
        curve_bounds = [
            (0.0, L + 5.0),
            (0.1, 2.0),
            (0.15, 2.2),
            (0.2, 3.0),
        ]
    else:
        curve_bounds = [
            (0.0, L + 5.0),
            (0.1, 2.0),
            (0.15, 2.2),
            (-1.8, 1.8),
            (-2.0, 2.0),
            (0.2, 3.0),
        ]

    global_result = differential_evolution(
        lambda z: simulate_curve(z, train_demands),
        bounds=curve_bounds,
        popsize=5,
        maxiter=12,
        tol=0.002,
        polish=False,
        seed=73 + L,
        workers=1,
        updating="immediate",
    )

    if L == 2:
        seeds = [
            global_result.x,
            np.array([base_stock_target, 1.0, 1.0, base_cap]),
        ]
    else:
        seeds = [
            global_result.x,
            np.array([
                base_stock_target, 1.0, 1.0, 0.0, 0.0, base_cap
            ]),
        ]

    response = (
        0.30
        + 0.70
        * ((10.0 - normalized_p) / 8.0)
        * ((L - 2.0) / 8.0)
    )
    slope = (
        0.15
        + 0.80
        * ((normalized_p - 2.0) / 8.0)
        * ((L - 2.0) / 8.0)
    )
    curvature = -0.6
    heuristic_cap = base_cap * (1.0 + 0.8 / L)

    if L == 2:
        seeds.extend([
            np.array([
                heuristic_cap * (2.0 * response + 0.6),
                response,
                response,
                heuristic_cap,
            ]),
            np.array([
                0.6 * base_stock_target,
                0.35,
                0.5,
                heuristic_cap,
            ]),
        ])
    else:
        positions = np.linspace(0.0, 1.0, L - 1)
        heuristic_weights = 1.15 * response * np.exp(
            slope * positions
            + curvature * positions * (1.0 - positions)
        )
        heuristic_intercept = heuristic_cap * (
            response + heuristic_weights.sum() + 0.4
        )
        seeds.extend([
            np.array([
                heuristic_intercept,
                response,
                1.15 * response,
                slope,
                curvature,
                heuristic_cap,
            ]),
            np.array([
                0.65 * base_stock_target,
                0.4,
                0.55,
                0.7,
                -0.5,
                heuristic_cap,
            ]),
        ])

    lower_curve = np.array([b[0] for b in curve_bounds])
    upper_curve = np.array([b[1] for b in curve_bounds])

    curve_candidates = []
    for index, seed in enumerate(seeds):
        seed = np.clip(seed, lower_curve, upper_curve)
        result = minimize(
            lambda z: simulate_curve(z, train_demands),
            seed,
            method="Powell",
            bounds=curve_bounds,
            options={
                "maxiter": 4 if index == 0 else 2,
                "xtol": 0.004,
                "ftol": 0.00015,
            },
        )
        curve_candidates.append(np.clip(
            result.x, lower_curve, upper_curve
        ))

    def curve_score(z):
        return (
            0.6 * simulate_curve(z, train_demands)
            + 0.4 * simulate_curve(z, validation_demands)
        )

    best_curve = min(curve_candidates, key=curve_score)

    if L == 2:
        initial_full = np.array([
            best_curve[0],
            best_curve[1],
            best_curve[2],
            best_curve[3],
        ])
    else:
        positions = np.linspace(0.0, 1.0, L - 1)
        initial_weights = best_curve[2] * np.exp(
            best_curve[3] * positions
            + best_curve[4] * positions * (1.0 - positions)
        )
        initial_full = np.concatenate((
            [best_curve[0], best_curve[1]],
            initial_weights,
            [best_curve[5]],
        ))

    full_bounds = (
        [(0.0, L + 5.0), (0.05, 2.5)]
        + [(0.05, 2.5)] * (L - 1)
        + [(0.2, 3.0)]
    )

    def simulate_full(y, demands, use_projection=False):
        intercept = y[0] * mean_demand
        inventory_weight = y[1]
        weights = y[2:2 + L - 1]
        if use_projection:
            projection_weight = y[-2]
        else:
            projection_weight = 0.0
        order_cap = y[-1] * mean_demand

        n = demands.shape[0]
        inventory = np.zeros(n)
        pipeline = np.zeros((n, L - 1))
        total_cost = 0.0

        for t in range(L + horizon):
            raw_order = (
                intercept
                - inventory_weight * inventory
                - pipeline @ weights
            )

            if use_projection and projection_weight > 0.0:
                projected = np.maximum(
                    inventory - rounded_mean, 0.0
                )
                for j in range(L - 1):
                    projected = np.maximum(
                        projected + pipeline[:, j] - rounded_mean,
                        0.0,
                    )
                raw_order -= projection_weight * projected

            orders = np.clip(raw_order, 0.0, order_cap)

            if t >= L:
                demand = demands[:, t - L]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                total_cost += np.mean(
                    inventory + cost_ratio * (demand - sales)
                )

            inventory += pipeline[:, 0]
            pipeline[:, :-1] = pipeline[:, 1:]
            pipeline[:, -1] = orders

        return float(total_cost)

    full_result = minimize(
        lambda y: simulate_full(y, train_demands, False),
        initial_full,
        method="Powell",
        bounds=full_bounds,
        options={
            "maxiter": 3,
            "xtol": 0.004,
            "ftol": 0.00012,
        },
    )
    refined_full = full_result.x

    def full_score(y):
        return (
            0.6 * simulate_full(y, train_demands, False)
            + 0.4 * simulate_full(y, validation_demands, False)
        )

    if full_score(refined_full) < full_score(initial_full):
        best_full = refined_full
    else:
        best_full = initial_full

    initial_projected = np.concatenate((
        best_full[:-1], [0.0, best_full[-1]]
    ))
    projection_bounds = (
        [(0.0, L + 5.0), (0.05, 2.5)]
        + [(0.05, 2.5)] * (L - 1)
        + [(0.0, 2.0), (0.2, 3.0)]
    )

    projection_result = minimize(
        lambda y: simulate_full(y, train_demands, True),
        initial_projected,
        method="Powell",
        bounds=projection_bounds,
        options={
            "maxiter": 3,
            "xtol": 0.004,
            "ftol": 0.00012,
        },
    )
    refined_projected = projection_result.x

    def projected_score(y):
        return (
            0.6 * simulate_full(y, train_demands, True)
            + 0.4 * simulate_full(y, validation_demands, True)
        )

    if projected_score(refined_projected) < projected_score(
        initial_projected
    ):
        final_parameters = refined_projected
    else:
        final_parameters = initial_projected

    intercept = float(final_parameters[0] * mean_demand)
    inventory_weight = float(final_parameters[1])
    pipeline_weights = tuple(
        float(x) for x in final_parameters[2:2 + L - 1]
    )
    projection_weight = float(final_parameters[-2])
    order_cap = float(final_parameters[-1] * mean_demand)
    projected_period_demand = float(rounded_mean)

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        inventory = float(on_hand_inventory)

        raw_order = intercept - inventory_weight * inventory
        projected_inventory = inventory - projected_period_demand
        if projected_inventory < 0.0:
            projected_inventory = 0.0

        for weight, outstanding in zip(
            pipeline_weights, pipeline_orders
        ):
            outstanding = float(outstanding)
            raw_order -= weight * outstanding
            projected_inventory += outstanding
            projected_inventory -= projected_period_demand
            if projected_inventory < 0.0:
                projected_inventory = 0.0

        if projection_weight > 0.0:
            raw_order -= projection_weight * projected_inventory

        if not (raw_order > 0.0):
            return 0.0
        if raw_order >= order_cap:
            return order_cap
        return float(raw_order)

    return compute_order_amount
