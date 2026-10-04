def design(params):
    import math
    import numpy as np
    from scipy.optimize import minimize
    from scipy.special import ndtr, ndtri

    lead_time = int(params["lead_time"])
    mean_demand = float(params["mean_demand"])
    holding_cost = float(params["holding_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    horizon = int(params["horizon"])

    sqrt_mean = math.sqrt(mean_demand)
    inv_sqrt_2pi = 0.39894228040143267794

    # Use a deterministic sample-average optimization to tune a stationary,
    # smoothed projected-inventory policy.
    episode_count = 10000
    rng = np.random.default_rng(731291)
    demands = rng.poisson(
        mean_demand, size=(episode_count, horizon)
    ).astype(np.float64)

    def sample_average_cost(x):
        buffer_target = float(x[0])
        feedback_gain = float(x[1])
        projection_shift = float(x[2])
        projected_demand = mean_demand + projection_shift * sqrt_mean

        if projected_demand <= 1.0 or not np.isfinite(projected_demand):
            return 1.0e100

        inventory = np.zeros(episode_count, dtype=np.float64)
        pipeline = np.zeros(
            (episode_count, lead_time - 1), dtype=np.float64
        )
        last_order = np.zeros(episode_count, dtype=np.float64)
        total_cost = 0.0

        for period in range(lead_time + horizon):
            if period > 0:
                inventory += pipeline[:, 0]
                if lead_time > 2:
                    pipeline[:, :-1] = pipeline[:, 1:]
                pipeline[:, -1] = last_order

            # Moment-matched projection of inventory remaining immediately
            # before the current order arrives.
            projected_mean = inventory.copy()
            projected_variance = np.zeros(episode_count, dtype=np.float64)

            for j in range(lead_time):
                net_mean = projected_mean - projected_demand
                net_sd = np.sqrt(projected_variance + projected_demand)
                a = net_mean / net_sd
                cdf = ndtr(a)
                density = np.exp(-0.5 * a * a) * inv_sqrt_2pi

                second_moment = (
                    (net_sd * net_sd + net_mean * net_mean) * cdf
                    + net_mean * net_sd * density
                )
                next_mean = net_sd * density + net_mean * cdf
                projected_variance = np.maximum(
                    second_moment - next_mean * next_mean, 0.0
                )
                projected_mean = next_mean

                if j < lead_time - 1:
                    projected_mean += pipeline[:, j]

            last_order = np.maximum(
                mean_demand
                + feedback_gain * (buffer_target - projected_mean),
                0.0,
            )

            if period >= lead_time:
                demand = demands[:, period - lead_time]
                lost = np.maximum(demand - inventory, 0.0)
                inventory = np.maximum(inventory - demand, 0.0)
                total_cost += (
                    holding_cost * inventory.sum()
                    + lost_sales_cost * lost.sum()
                )

        value = total_cost / episode_count
        return float(value) if np.isfinite(value) else 1.0e100

    critical_ratio = lost_sales_cost / (
        lost_sales_cost + holding_cost
    )
    z_value = float(ndtri(critical_ratio))

    initial_x = np.array(
        [
            0.75 * z_value * sqrt_mean,
            0.90,
            0.20,
        ],
        dtype=np.float64,
    )

    bounds = [
        (-2.0 * sqrt_mean, 5.0 * sqrt_mean),
        (0.10, 1.60),
        (-0.50, 1.00),
    ]

    initial_value = sample_average_cost(initial_x)

    try:
        result = minimize(
            sample_average_cost,
            initial_x,
            method="L-BFGS-B",
            bounds=bounds,
            options={
                "maxiter": 18,
                "maxfun": 88,
                "maxls": 10,
                "ftol": 1.0e-8,
                "gtol": 1.0e-4,
            },
        )
        if (
            np.all(np.isfinite(result.x))
            and np.isfinite(result.fun)
            and result.fun <= initial_value
        ):
            chosen_x = result.x
        else:
            chosen_x = initial_x
    except Exception:
        chosen_x = initial_x

    buffer_target = float(chosen_x[0])
    feedback_gain = float(chosen_x[1])
    projection_shift = float(chosen_x[2])
    projected_demand = max(
        1.0, mean_demand + projection_shift * sqrt_mean
    )

    sqrt_two = math.sqrt(2.0)
    huge_state = 1.0e100

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        current_inventory = float(on_hand_inventory)

        # This also prevents overflow for valid but extremely large states.
        if current_inventory >= huge_state:
            return 0.0

        pipeline = [float(v) for v in pipeline_orders]
        for value in pipeline:
            if value >= huge_state:
                return 0.0

        projected_mean = current_inventory
        projected_variance = 0.0

        for j in range(lead_time):
            net_mean = projected_mean - projected_demand
            net_sd = math.sqrt(projected_variance + projected_demand)
            a = net_mean / net_sd

            if a <= -8.0:
                next_mean = 0.0
                next_variance = 0.0
            elif a >= 8.0:
                next_mean = net_mean
                next_variance = net_sd * net_sd
            else:
                cdf = 0.5 * (
                    1.0 + math.erf(a / sqrt_two)
                )
                density = math.exp(-0.5 * a * a) * inv_sqrt_2pi
                second_moment = (
                    (net_sd * net_sd + net_mean * net_mean) * cdf
                    + net_mean * net_sd * density
                )
                next_mean = net_sd * density + net_mean * cdf
                next_variance = max(
                    second_moment - next_mean * next_mean, 0.0
                )

            projected_mean = next_mean
            projected_variance = next_variance

            if j < lead_time - 1:
                projected_mean += pipeline[j]

        order = mean_demand + feedback_gain * (
            buffer_target - projected_mean
        )

        if order <= 0.0:
            return 0.0
        if not math.isfinite(order):
            return 0.0
        return float(order)

    return compute_order_amount
