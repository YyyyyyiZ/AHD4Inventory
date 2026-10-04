def design(params):
    import math
    import numpy as np
    from scipy.optimize import differential_evolution, minimize_scalar
    from scipy.special import ndtri, pdtr

    L = int(params["lead_time"])
    mean_demand = float(params["mean_demand"])
    holding_cost = float(params["holding_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    horizon = int(params["horizon"])

    sqrt_mean = math.sqrt(mean_demand)

    # Table for E[(x-D)^+], D ~ Poisson(mean_demand), for real x.
    table_limit = int(math.ceil(mean_demand + 12.0 * sqrt_mean + 20.0))
    indices = np.arange(table_limit + 1)
    poisson_cdf = np.asarray(pdtr(indices, mean_demand), dtype=float)
    preceding_cdf = np.empty_like(poisson_cdf)
    preceding_cdf[0] = 0.0
    preceding_cdf[1:] = poisson_cdf[:-1]

    def expected_leftover_vector(x):
        x = np.asarray(x, dtype=float)
        n = np.floor(x).astype(np.int64)
        clipped = np.clip(n, 0, table_limit)
        result = (
            x * poisson_cdf[clipped]
            - mean_demand * preceding_cdf[clipped]
        )
        result = np.where(n < 0, 0.0, result)
        result = np.where(n > table_limit, np.maximum(0.0, x - mean_demand), result)
        return result

    # Optimize a capped projected-inventory-level policy by common-random-number
    # simulation. The cap is a policy parameter, not a physical order capacity.
    simulation_episodes = 9000
    rng = np.random.default_rng(104729)
    selling_demands = rng.poisson(
        mean_demand, size=(simulation_episodes, horizon)
    )

    def simulated_cost(theta):
        target = float(theta[0])
        order_cap = float(theta[1])

        inventory = np.zeros(simulation_episodes, dtype=float)

        # Before the arrival event there are L arrival slots. After popping the
        # current arrival, the remaining L-1 entries are exactly the observed
        # pipeline.
        future_orders = [
            np.zeros(simulation_episodes, dtype=float) for _ in range(L)
        ]

        total_cost = 0.0

        for period in range(-L, horizon):
            inventory += future_orders.pop(0)

            # Approximate expected inventory immediately before the new order's
            # arrival, accounting for lost sales at each intervening period.
            projected = expected_leftover_vector(inventory)
            for arrival in future_orders:
                projected = expected_leftover_vector(projected + arrival)

            order = np.minimum(
                order_cap, np.maximum(0.0, target - projected)
            )
            future_orders.append(order)

            if period >= 0:
                demand = selling_demands[:, period]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                lost = demand - sales
                total_cost += np.mean(
                    holding_cost * inventory + lost_sales_cost * lost
                )

        return float(total_cost)

    critical_ratio = lost_sales_cost / (lost_sales_cost + holding_cost)
    fallback_target = mean_demand + sqrt_mean * float(ndtri(critical_ratio))
    fallback_target = max(0.0, fallback_target)

    target_lower = max(0.0, mean_demand - 5.0 * sqrt_mean)
    target_upper = mean_demand + 7.0 * sqrt_mean
    cap_lower = max(1e-9, mean_demand - 5.0 * sqrt_mean)
    cap_upper = mean_demand + 8.0 * sqrt_mean

    best_target = min(max(fallback_target, target_lower), target_upper)
    best_cap = cap_upper
    best_cost = simulated_cost((best_target, best_cap))

    try:
        # First obtain a reliable uncapped projected-inventory-level candidate.
        scalar_result = minimize_scalar(
            lambda u: simulated_cost((float(u), cap_upper)),
            bounds=(target_lower, target_upper),
            method="bounded",
            options={"xatol": 0.02, "maxiter": 50},
        )
        if scalar_result.success and math.isfinite(scalar_result.fun):
            candidate_target = float(scalar_result.x)
            candidate_cost = float(scalar_result.fun)
            if candidate_cost < best_cost:
                best_target = candidate_target
                best_cap = cap_upper
                best_cost = candidate_cost

        # Joint optimization can improve startup and high-penalty behavior by
        # limiting exceptionally large replenishment orders.
        joint_result = differential_evolution(
            simulated_cost,
            bounds=((target_lower, target_upper), (cap_lower, cap_upper)),
            seed=130363,
            popsize=6,
            maxiter=10,
            tol=0.003,
            polish=True,
            workers=1,
            updating="immediate",
        )
        if joint_result.success or math.isfinite(joint_result.fun):
            candidate_target = float(joint_result.x[0])
            candidate_cap = float(joint_result.x[1])
            candidate_cost = simulated_cost(
                (candidate_target, candidate_cap)
            )
            if math.isfinite(candidate_cost) and candidate_cost < best_cost:
                best_target = candidate_target
                best_cap = candidate_cap
                best_cost = candidate_cost
    except Exception:
        pass

    if not math.isfinite(best_target) or best_target < 0.0:
        best_target = fallback_target
    if not math.isfinite(best_cap) or best_cap <= 0.0:
        best_cap = cap_upper

    target = float(best_target)
    order_cap = float(best_cap)

    def expected_leftover_scalar(x):
        if not math.isfinite(x):
            return x
        if x <= 0.0:
            return 0.0
        if x > table_limit:
            return max(0.0, x - mean_demand)

        n = int(math.floor(x))
        return max(
            0.0,
            x * float(poisson_cdf[n])
            - mean_demand * float(preceding_cdf[n]),
        )

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        projected = expected_leftover_scalar(float(on_hand_inventory))

        for arrival in pipeline_orders:
            arrival = float(arrival)
            if math.isinf(projected):
                break
            projected = expected_leftover_scalar(projected + arrival)

        raw_order = target - projected
        if not math.isfinite(raw_order):
            return 0.0 if raw_order < 0.0 else order_cap
        if raw_order <= 0.0:
            return 0.0
        if raw_order >= order_cap:
            return order_cap
        return float(raw_order)

    return compute_order_amount
