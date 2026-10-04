def design(params):
    import math
    import numpy as np
    from scipy.optimize import differential_evolution
    from scipy.special import ndtr, ndtri

    L = int(params["lead_time"])
    mu = float(params["mean_demand"])
    sigma = float(params["std_normal"])
    h = float(params["holding_cost"])
    p = float(params["lost_sales_cost"])
    horizon = int(params["horizon"])

    # Exact-enough moments and CDF of the clipped-and-rounded demand law.
    # D=0 when X<0.5, and D=k has interval [k-0.5,k+0.5) for k>=1.
    max_d = max(20, int(math.ceil(mu + 10.0 * sigma)) + 2)
    demand_values = np.arange(max_d + 1, dtype=float)
    edge_cdf = ndtr((demand_values + 0.5 - mu) / sigma)
    probabilities = np.empty(max_d + 1, dtype=float)
    probabilities[0] = edge_cdf[0]
    probabilities[1:] = np.diff(edge_cdf)
    probabilities[-1] += 1.0 - probabilities.sum()

    demand_mean = float(probabilities @ demand_values)
    demand_second = float(probabilities @ (demand_values * demand_values))
    demand_variance = max(1.0e-12, demand_second - demand_mean * demand_mean)
    demand_sd = math.sqrt(demand_variance)

    cumulative_probability = np.cumsum(probabilities)
    critical_fractile = p / max(p + h, 1.0e-12)
    initial_target = float(
        np.searchsorted(cumulative_probability, critical_fractile, side="left")
    )

    # Deterministic common-random-number training panel. Each period uses a
    # separately shuffled Latin hypercube.
    sample_count = 4096
    rng = np.random.default_rng(731927)
    uniforms = (
        np.arange(sample_count, dtype=float)[:, None]
        + rng.random((sample_count, horizon))
    ) / sample_count
    for column in range(horizon):
        rng.shuffle(uniforms[:, column])

    selling_demands = np.rint(
        np.maximum(0.0, mu + sigma * ndtri(uniforms))
    )

    inv_sqrt_2pi = 1.0 / math.sqrt(2.0 * math.pi)

    # Policy family:
    #
    # 1. Approximate the conditional mean inventory immediately before the
    #    new order arrives. A two-moment normal closure is used at each
    #    intervening demand epoch.
    # 2. Order according to a projected-inventory feedback rule.
    # 3. A small autoregressive term based on the most recent order suppresses
    #    order oscillations and also gives sensible pipeline initialization.
    #
    # The simulation below includes the L zero-demand planning periods.
    def objective(theta):
        A = float(theta[0])
        gain = float(theta[1])
        smoothing = float(theta[2])

        inventory = np.zeros(sample_count, dtype=float)
        pipeline = np.zeros((sample_count, L - 1), dtype=float)
        total_cost = 0.0

        for period in range(L + horizon):
            projected_mean = inventory.copy()
            projected_variance = np.zeros(sample_count, dtype=float)

            for step in range(L):
                normal_mean = projected_mean - demand_mean
                normal_sd = np.sqrt(
                    np.maximum(projected_variance + demand_variance, 1.0e-12)
                )
                z = normal_mean / normal_sd
                cdf = ndtr(z)
                density = np.exp(-0.5 * z * z) * inv_sqrt_2pi

                projected_second = (
                    (normal_mean * normal_mean + normal_sd * normal_sd) * cdf
                    + normal_mean * normal_sd * density
                )
                projected_mean = normal_sd * density + normal_mean * cdf
                projected_variance = np.maximum(
                    0.0,
                    projected_second - projected_mean * projected_mean,
                )

                if step < L - 1:
                    projected_mean += pipeline[:, step]

            newest_pipeline_order = pipeline[:, -1]
            order = np.maximum(
                0.0,
                A
                - gain * projected_mean
                - smoothing * (newest_pipeline_order - demand_mean),
            )

            if period >= L:
                demand = selling_demands[:, period - L]
                sales = np.minimum(inventory, demand)
                inventory -= sales
                lost = demand - sales
                total_cost += h * float(inventory.mean()) + p * float(lost.mean())

            # Advance one period: receive what is currently one period away,
            # shift the remaining pipeline, and append this period's order.
            inventory += pipeline[:, 0]
            if L > 2:
                pipeline[:, :-1] = pipeline[:, 1:]
            pipeline[:, -1] = order

        return total_cost

    A_upper = max(
        initial_target + demand_sd,
        demand_mean + 4.0 * demand_sd + 1.0,
    )
    bounds = [
        (0.0, A_upper),
        (0.08, 1.60),
        (0.0, 0.45),
    ]

    initial_gain = min(1.25, 0.55 + 0.35 * math.sqrt(2.0 / L))
    x0 = np.array(
        [
            min(max(initial_target, 0.0), A_upper),
            initial_gain,
            0.05,
        ],
        dtype=float,
    )

    try:
        result = differential_evolution(
            objective,
            bounds,
            seed=24680,
            x0=x0,
            popsize=6,
            maxiter=9,
            tol=0.004,
            atol=0.02,
            mutation=(0.5, 1.0),
            recombination=0.75,
            polish=True,
            workers=1,
            updating="immediate",
        )
        if result.success or np.isfinite(result.fun):
            A, gain, smoothing = map(float, result.x)
        else:
            A, gain, smoothing = map(float, x0)
    except Exception:
        A, gain, smoothing = map(float, x0)

    # Avoid overflow for arbitrary but finite states far outside the range
    # relevant to the instance. Such states clearly require no new order.
    huge_state = 1.0e100
    sqrt_two = math.sqrt(2.0)

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        inventory = float(on_hand_inventory)
        pipeline = np.asarray(pipeline_orders, dtype=float).reshape(-1)

        if inventory > huge_state or np.any(pipeline > huge_state):
            return 0.0

        projected_mean = max(0.0, inventory)
        projected_variance = 0.0

        for step in range(L):
            normal_mean = projected_mean - demand_mean
            normal_variance = projected_variance + demand_variance
            normal_sd = math.sqrt(max(normal_variance, 1.0e-12))
            z = normal_mean / normal_sd

            if z >= 8.0:
                projected_mean = normal_mean
                projected_variance = normal_variance
            elif z <= -8.0:
                projected_mean = 0.0
                projected_variance = 0.0
            else:
                cdf = 0.5 * (1.0 + math.erf(z / sqrt_two))
                density = math.exp(-0.5 * z * z) * inv_sqrt_2pi
                projected_second = (
                    (normal_mean * normal_mean + normal_variance) * cdf
                    + normal_mean * normal_sd * density
                )
                projected_mean = normal_sd * density + normal_mean * cdf
                projected_variance = max(
                    0.0,
                    projected_second - projected_mean * projected_mean,
                )

            if step < L - 1:
                projected_mean += float(pipeline[step])

        newest_pipeline_order = float(pipeline[-1])
        order = (
            A
            - gain * projected_mean
            - smoothing * (newest_pipeline_order - demand_mean)
        )

        if not math.isfinite(order) or order <= 0.0:
            return 0.0
        return float(order)

    return compute_order_amount
