def design(params):
    import numpy as np
    from numba import njit

    scenario = scenario_from_params(params)
    m = int(scenario.m)
    cv = float(scenario.cv)
    f = float(scenario.f)
    cap = int(inventory_cap(scenario))

    cv_key = 1.5 if abs(cv - 1.5) < abs(cv - 2.0) else 2.0
    f_key = 0.0 if f < 0.25 else 0.5

    # Robust starting policies for m=7. Layout:
    # [target, maximum_order, age_weights..., pipeline_weight]
    starts7 = {
        (1.5, 0.0): np.array([
            22.687, 19.929,
            0.104, 0.100, 2.119, 2.352, 1.668, 1.436, 1.253,
            1.113
        ], dtype=np.float64),
        (2.0, 0.0): np.array([
            20.319, 18.259,
            0.346, 0.155, 2.362, 2.396, 1.819, 1.767, 1.214,
            1.078
        ], dtype=np.float64),
        (1.5, 0.5): np.array([
            15.0483, 23.3912,
            0.2459, 0.3025, 0.5958, 0.6377, 0.7124, 0.8242, 0.7121,
            0.9500
        ], dtype=np.float64),
        (2.0, 0.5): np.array([
            11.2965, 7.0137,
            0.2384, 0.1460, 0.5489, 0.6456, 0.5011, 0.4905, 0.7085,
            0.7460
        ], dtype=np.float64),
    }

    base7 = starts7[(cv_key, f_key)].copy()

    if m == 7:
        initial = base7
    else:
        # Preserve weights by remaining life. The extra fresh slot gets a
        # moderate marginal-inventory weight.
        target_increment = 3.0 if f_key == 0.0 else 2.0
        fresh_weight = 1.05 if f_key == 0.0 else 0.80
        initial = np.empty(m + 3, dtype=np.float64)
        initial[0] = min(float(cap), base7[0] + target_increment)
        initial[1] = min(float(cap), base7[1] + 1.0)
        initial[2:9] = base7[2:9]
        if m > 8:
            initial[9:2 + m] = fresh_weight
        else:
            initial[9] = fresh_weight
        initial[2 + m] = base7[-1]

    initial[0] = np.clip(initial[0], 4.0, float(cap))
    initial[1] = np.clip(initial[1], 1.0, float(cap))

    @njit
    def parameterized_policy(age, pipeline, theta, mu, policy_cv,
                             fifo_fraction, lead_time):
        z = theta[0]
        n = len(age)

        for i in range(n):
            z -= theta[2 + i] * age[i]

        pipe_weight = theta[2 + n]
        for i in range(len(pipeline)):
            z -= pipe_weight * pipeline[i]

        if z <= 0.0:
            return 0.0
        if z >= theta[1]:
            return theta[1]
        return z

    candidates = [initial.copy()]

    try:
        seed_code = (
            931700
            + 1000 * m
            + 100 * int(round(2.0 * cv))
            + 10 * int(round(2.0 * f))
        )
        train = sample_demands(
            scenario, npaths=56, periods=1800, seed=seed_code
        )

        def objective(theta):
            path_costs, _ = evaluate(
                scenario, train, parameterized_policy, theta, burnin=500
            )
            return float(np.mean(path_costs))

        bounds = (
            [(6.0, float(cap)), (2.0, float(cap))]
            + [(0.0, 3.2)] * m
            + [(0.0, 2.0)]
        )

        result = optimize(
            objective,
            bounds,
            initial,
            budget=1024,
            seed=seed_code + 37
        )
        optimized = np.asarray(result["theta"], dtype=np.float64)

        # Include shrinkage candidates, which are often more robust than the
        # raw simulation optimizer when action rounding makes the objective
        # locally irregular.
        candidates.append(optimized)
        candidates.append(0.50 * initial + 0.50 * optimized)
        candidates.append(0.25 * initial + 0.75 * optimized)

        # A conventional age-discount policy supplies a structurally
        # different fallback candidate.
        fitted = {
            (1.5, 0.0): (16.8236222705, 18.5614041716, 0.0555249661),
            (1.5, 0.5): (16.2972109285, 20.3012221938, 0.9076730990),
            (2.0, 0.0): (15.1172852932, 28.5471514156, 0.0325568594),
            (2.0, 0.5): (13.9831632050, 5.8901227839, 1.0672962231),
        }
        s0, c0, exponent = fitted[(cv_key, f_key)]
        conventional = np.empty(m + 3, dtype=np.float64)
        conventional[0] = min(cap, s0 + 2.25 * (m - 7))
        conventional[1] = min(cap, c0 + 0.5 * (m - 7))
        for i in range(m):
            conventional[2 + i] = ((i + 1.0) / m) ** exponent
        conventional[2 + m] = 1.0
        candidates.append(conventional)

        # Select on an independent exact-law simulation. Common random
        # numbers make pairwise policy comparisons substantially less noisy.
        validation = sample_demands(
            scenario, npaths=64, periods=3000, seed=seed_code + 104729
        )
        validation_scores = []
        for candidate in candidates:
            path_costs, _ = evaluate(
                scenario,
                validation,
                parameterized_policy,
                candidate,
                burnin=500
            )
            validation_scores.append(float(np.mean(path_costs)))

        best_index = int(np.argmin(np.asarray(validation_scores)))
        # Require a small improvement over the robust starting policy before
        # accepting a simulation-tuned replacement.
        if (
            best_index != 0
            and validation_scores[0] - validation_scores[best_index] < 0.20
        ):
            best_index = 0
        theta = candidates[best_index].copy()

    except Exception:
        theta = initial.copy()

    target = float(theta[0])
    maximum_order = float(theta[1])
    age_weights = np.asarray(theta[2:2 + m], dtype=np.float64).copy()
    pipeline_weight = float(theta[2 + m])

    def policy(age, pipeline):
        effective = 0.0
        for i in range(m):
            effective += age_weights[i] * float(age[i])
        for i in range(len(pipeline)):
            effective += pipeline_weight * float(pipeline[i])

        q = target - effective
        if q <= 0.0:
            return 0.0
        if q >= maximum_order:
            return maximum_order
        return q

    return policy
