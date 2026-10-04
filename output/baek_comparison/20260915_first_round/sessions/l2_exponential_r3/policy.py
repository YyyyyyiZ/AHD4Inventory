def design(params):
    import math
    import numpy as np
    from scipy.optimize import minimize
    from scipy.stats import qmc

    lead_time = int(params["lead_time"])
    mean_demand = float(params["mean_demand"])
    holding_cost = float(params["holding_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    horizon = int(params["horizon"])

    penalty_ratio = lost_sales_cost / holding_cost
    log_ratio = math.log1p(penalty_ratio)

    # Deterministic quasi-Monte Carlo demand sample used only during design.
    sample_power = 14
    uniforms = qmc.Sobol(
        d=horizon, scramble=True, seed=22031991
    ).random_base2(sample_power)
    uniforms = np.minimum(uniforms, np.nextafter(1.0, 0.0))
    sampled_demand = np.rint(-mean_demand * np.log1p(-uniforms))
    del uniforms
    sample_count = sampled_demand.shape[0]

    def objective(log_parameters):
        initial_order = mean_demand * math.exp(float(log_parameters[0]))
        intercept = mean_demand * math.exp(float(log_parameters[1]))
        feedback_gain = math.exp(float(log_parameters[2]))

        inventory = np.zeros(sample_count, dtype=float)
        order_queue = [
            np.zeros(sample_count, dtype=float) for _ in range(lead_time)
        ]
        total_cost = 0.0

        for period in range(lead_time + horizon):
            inventory += order_queue.pop(0)

            all_zero = inventory == 0.0
            for outstanding in order_queue:
                all_zero &= outstanding == 0.0

            # Approximate expected inventory immediately before the new
            # order arrives. For exponential demand,
            # E[(x-D)^+] = x + mean*expm1(-x/mean).
            projected = inventory.copy()
            for j in range(lead_time):
                projected += mean_demand * np.expm1(
                    -projected / mean_demand
                )
                np.maximum(projected, 0.0, out=projected)
                if j < lead_time - 1:
                    projected += order_queue[j]

            new_order = np.maximum(
                0.0, intercept - feedback_gain * projected
            )
            new_order[all_zero] = initial_order
            order_queue.append(new_order)

            if period >= lead_time:
                demand = sampled_demand[:, period - lead_time]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                lost = demand - sales
                total_cost += float(
                    np.mean(
                        holding_cost * inventory
                        + lost_sales_cost * lost
                    )
                )

        return total_cost

    horizon_adjustment = 0.018 * (lead_time - 2)
    target_factor = max(
        0.45,
        0.90 + 0.035 * penalty_ratio - horizon_adjustment,
    )
    initial_ratio = max(
        0.36,
        0.80 * log_ratio * (1.0 - 0.006 * (lead_time - 2)),
    )

    starts = []
    for starting_gain in (1.0, 0.58):
        threshold_ratio = max(0.25, log_ratio * target_factor)
        intercept_ratio = max(
            0.21, starting_gain * threshold_ratio
        )
        starts.append(
            np.log(
                [
                    initial_ratio,
                    intercept_ratio,
                    starting_gain,
                ]
            )
        )

    bounds = [
        (math.log(0.35), math.log(3.5)),
        (math.log(0.20), math.log(4.0)),
        (math.log(0.30), math.log(1.05)),
    ]

    best_result = None
    for start in starts:
        result = minimize(
            objective,
            start,
            method="Nelder-Mead",
            bounds=bounds,
            options={
                "maxiter": 110,
                "maxfev": 135,
                "xatol": 0.003,
                "fatol": 0.15,
                "adaptive": True,
            },
        )
        if (
            math.isfinite(float(result.fun))
            and (
                best_result is None
                or float(result.fun) < float(best_result.fun)
            )
        ):
            best_result = result

    if best_result is None:
        optimized = starts[0]
    else:
        optimized = best_result.x

    initial_order = mean_demand * math.exp(float(optimized[0]))
    intercept = mean_demand * math.exp(float(optimized[1]))
    feedback_gain = math.exp(float(optimized[2]))

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        inventory = float(on_hand_inventory)
        pipeline = [float(x) for x in pipeline_orders]

        if inventory == 0.0 and all(x == 0.0 for x in pipeline):
            return float(initial_order)

        projected = inventory
        for j in range(lead_time):
            if math.isinf(projected):
                return 0.0

            projected += mean_demand * math.expm1(
                -projected / mean_demand
            )
            if projected < 0.0:
                projected = 0.0

            if j < lead_time - 1:
                projected += pipeline[j]

        order = intercept - feedback_gain * projected
        if not math.isfinite(order) or order <= 0.0:
            return 0.0
        return float(order)

    return compute_order_amount
