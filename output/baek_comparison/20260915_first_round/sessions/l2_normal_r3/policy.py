def design(params):
    import math
    import numpy as np
    from scipy.optimize import differential_evolution
    from scipy.special import ndtr, ndtri
    from scipy.stats import qmc

    L = int(params["lead_time"])
    latent_mean = float(params["mean_demand"])
    latent_std = float(params["std_normal"])
    holding_cost = float(params["holding_cost"])
    lost_sales_cost = float(params["lost_sales_cost"])
    horizon = int(params["horizon"])

    # Exact rounded/clipped demand distribution, with a negligible upper tail
    # consolidated into the final table entry.
    max_demand = int(math.ceil(latent_mean + 10.0 * latent_std + 10.0))
    demand_values = np.arange(max_demand + 1, dtype=float)
    probabilities = np.empty(max_demand + 1, dtype=float)

    probabilities[0] = ndtr((0.5 - latent_mean) / latent_std)
    k_values = demand_values[1:]
    probabilities[1:] = (
        ndtr((k_values + 0.5 - latent_mean) / latent_std)
        - ndtr((k_values - 0.5 - latent_mean) / latent_std)
    )
    probabilities = np.maximum(probabilities, 0.0)
    probabilities[-1] += 1.0 - probabilities.sum()
    probabilities = np.maximum(probabilities, 0.0)
    probabilities /= probabilities.sum()

    cumulative_probability = np.cumsum(probabilities)
    cumulative_first_moment = np.cumsum(probabilities * demand_values)
    cumulative_second_moment = np.cumsum(
        probabilities * demand_values * demand_values
    )
    mean_demand = float(cumulative_first_moment[-1])

    # For deterministic stock y, obtain the first two moments of (y-D)^+.
    def leftover_moments_vector(y):
        indices = np.ceil(y).astype(np.int64) - 1
        indices = np.clip(indices, 0, max_demand)

        f = cumulative_probability[indices]
        m1 = cumulative_first_moment[indices]
        m2 = cumulative_second_moment[indices]

        first = y * f - m1
        second = y * y * f - 2.0 * y * m1 + m2
        return np.maximum(first, 0.0), np.maximum(second, 0.0)

    # Deterministic, instance-specific quasi-Monte Carlo training paths.
    total_exponent = 12 if L <= 3 else 11
    half_exponent = total_exponent - 1

    uniforms_1 = qmc.Sobol(
        d=horizon, scramble=True, seed=1729
    ).random_base2(half_exponent)
    uniforms_2 = qmc.Sobol(
        d=horizon, scramble=True, seed=7919
    ).random_base2(half_exponent)
    uniforms = np.concatenate((uniforms_1, uniforms_2), axis=0)

    training_demands = np.rint(
        np.maximum(0.0, latent_mean + latent_std * ndtri(uniforms))
    )
    episode_count = training_demands.shape[0]

    # Policy form:
    # q = [B E[D] - gain E[I just before arrival]
    #      + risk_weight SD[I just before arrival]] clipped to [0,4E[D]].
    #
    # Future inventory moments are propagated by a nonnegative two-point
    # moment approximation. variance_memory controls how much conditional
    # variance is retained from one projected period to the next.
    def simulate_policy(theta):
        target_ratio, gain, risk_weight, variance_memory = theta

        inventory = np.zeros(episode_count, dtype=float)
        pipeline = np.zeros((episode_count, L - 1), dtype=float)
        total_cost = 0.0
        order_cap = 4.0 * mean_demand
        intercept = target_ratio * mean_demand

        for period in range(L + horizon):
            projected_mean = inventory.copy()
            projected_variance = np.zeros(episode_count, dtype=float)

            for j in range(L):
                positive = projected_mean > 1e-12
                representative_stock = projected_mean.copy()
                representative_probability = np.ones(
                    episode_count, dtype=float
                )

                representative_stock[positive] = (
                    projected_mean[positive]
                    + variance_memory
                    * projected_variance[positive]
                    / projected_mean[positive]
                )
                representative_probability[positive] = (
                    projected_mean[positive]
                    / representative_stock[positive]
                )

                first, second = leftover_moments_vector(
                    representative_stock
                )
                next_mean = representative_probability * first
                next_second = representative_probability * second
                next_variance = np.maximum(
                    next_second - next_mean * next_mean, 0.0
                )

                projected_mean = next_mean
                projected_variance = next_variance

                if j < L - 1:
                    projected_mean += pipeline[:, j]

            orders = np.clip(
                intercept
                - gain * projected_mean
                + risk_weight * np.sqrt(projected_variance),
                0.0,
                order_cap,
            )

            if period < L:
                demand = 0.0
            else:
                demand = training_demands[:, period - L]

            sales = np.minimum(inventory, demand)
            inventory -= sales

            if period >= L:
                total_cost += np.mean(
                    holding_cost * inventory
                    + lost_sales_cost * (demand - sales)
                )

            inventory += pipeline[:, 0]
            if L > 2:
                pipeline[:, :-1] = pipeline[:, 1:]
            pipeline[:, -1] = orders

        return float(total_cost)

    critical_fractile = lost_sales_cost / (
        lost_sales_cost + holding_cost
    )
    critical_index = int(
        np.searchsorted(
            cumulative_probability, critical_fractile, side="left"
        )
    )
    critical_ratio = max(
        0.3, float(critical_index) / max(mean_demand, 1e-12)
    )

    initial_theta = np.array(
        [
            min(4.5, 1.0 + 0.7 * (critical_ratio - 1.0)),
            max(0.25, 0.8 / math.sqrt(max(1.0, L / 2.0))),
            0.0,
            0.5,
        ],
        dtype=float,
    )

    target_upper = max(
        3.0, min(5.0, 1.5 * critical_ratio + 0.5)
    )
    bounds = [
        (0.3, target_upper),
        (0.0, 2.0),
        (-2.0, 2.0),
        (0.0, 1.5),
    ]
    initial_theta = np.array(
        [
            np.clip(initial_theta[i], bounds[i][0], bounds[i][1])
            for i in range(4)
        ],
        dtype=float,
    )

    if L <= 3:
        maximum_iterations = 16
    elif L <= 7:
        maximum_iterations = 14
    else:
        maximum_iterations = 12

    try:
        result = differential_evolution(
            simulate_policy,
            bounds=bounds,
            strategy="best1bin",
            maxiter=maximum_iterations,
            popsize=6,
            tol=0.006,
            atol=0.0,
            mutation=(0.5, 1.0),
            recombination=0.7,
            seed=314159,
            polish=True,
            init="latinhypercube",
            x0=initial_theta,
            updating="immediate",
            workers=1,
        )
        theta = np.asarray(result.x, dtype=float)
        if theta.shape != (4,) or not np.all(np.isfinite(theta)):
            theta = initial_theta
    except Exception:
        theta = initial_theta

    target_ratio = float(theta[0])
    gain = float(theta[1])
    risk_weight = float(theta[2])
    variance_memory = float(theta[3])
    intercept = target_ratio * mean_demand
    order_cap = 4.0 * mean_demand
    large_state_threshold = 1e9 * (
        1.0 + mean_demand + latent_std + max_demand
    )

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        inventory = float(on_hand_inventory)
        pipeline = tuple(float(x) for x in pipeline_orders)

        if len(pipeline) != L - 1:
            return 0.0
        if not math.isfinite(inventory) or inventory < 0.0:
            return 0.0
        for value in pipeline:
            if not math.isfinite(value) or value < 0.0:
                return 0.0
            if value > large_state_threshold:
                return 0.0
        if inventory > large_state_threshold:
            return 0.0

        projected_mean = inventory
        projected_variance = 0.0

        for j in range(L):
            if projected_mean > 1e-12:
                representative_stock = (
                    projected_mean
                    + variance_memory
                    * projected_variance
                    / projected_mean
                )
                representative_probability = (
                    projected_mean / representative_stock
                )
            else:
                representative_stock = 0.0
                representative_probability = 1.0

            if (
                not math.isfinite(representative_stock)
                or representative_stock > large_state_threshold
            ):
                return 0.0

            index = int(math.ceil(representative_stock) - 1)
            if index < 0:
                index = 0
            elif index > max_demand:
                index = max_demand

            f = float(cumulative_probability[index])
            d1 = float(cumulative_first_moment[index])
            d2 = float(cumulative_second_moment[index])

            first = representative_stock * f - d1
            second = (
                representative_stock * representative_stock * f
                - 2.0 * representative_stock * d1
                + d2
            )
            if first < 0.0:
                first = 0.0
            if second < 0.0:
                second = 0.0

            next_mean = representative_probability * first
            next_second = representative_probability * second
            next_variance = next_second - next_mean * next_mean

            projected_mean = max(0.0, next_mean)
            projected_variance = max(0.0, next_variance)

            if j < L - 1:
                projected_mean += pipeline[j]

        order = (
            intercept
            - gain * projected_mean
            + risk_weight * math.sqrt(projected_variance)
        )

        if not math.isfinite(order) or order <= 0.0:
            return 0.0
        if order >= order_cap:
            return float(order_cap)
        return float(order)

    return compute_order_amount
