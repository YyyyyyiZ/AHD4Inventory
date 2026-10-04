def design(params):
    import math
    import numpy as np
    from scipy.special import ndtr, ndtri
    from scipy.stats import qmc
    from scipy.optimize import differential_evolution, minimize, minimize_scalar

    L = int(params["lead_time"])
    H = int(params["horizon"])
    mu = float(params["mean_demand"])
    sigma = float(params["std_normal"])
    hold = float(params["holding_cost"])
    penalty = float(params["lost_sales_cost"])

    # Exact discrete distribution, apart from a negligible upper tail.
    mmax = max(64, int(math.ceil(mu + 9.0 * sigma + 16.0)))
    dvals = np.arange(mmax + 1, dtype=float)
    dcdf = ndtr((dvals + 0.5 - mu) / sigma)

    pmf = np.empty(mmax + 1, dtype=float)
    pmf[0] = dcdf[0]
    pmf[1:] = np.diff(dcdf)

    cumprob = np.cumsum(pmf)
    cumfirst = np.cumsum(pmf * dvals)
    mean_d = float(cumfirst[-1])
    second_d = float(np.dot(pmf, dvals * dvals))
    var_d = max(1.0e-12, second_d - mean_d * mean_d)

    upper_a = max(3.5, (mu + 4.0 * sigma) / max(mean_d, 1.0))

    def make_demands(power, seed):
        u = qmc.Sobol(d=H, scramble=True, seed=seed).random_base2(power)
        return np.rint(np.maximum(0.0, mu + sigma * ndtri(u)))

    train_demands = make_demands(11, 1927)

    def evaluate(z, demands):
        ar, b, c, w = [float(v) for v in z]
        if not (
            0.04 <= ar <= upper_a
            and 0.0 <= b <= 2.25
            and 0.0 <= c <= 0.85
            and 0.0 <= w <= 1.0
        ):
            return 1.0e100

        target = ar * mean_d
        nrep = demands.shape[0]
        inv = np.zeros(nrep, dtype=float)
        pipe = np.zeros((nrep, L - 1), dtype=float)
        total = 0.0

        for t in range(L + H):
            # Mean projected inventory just before the new order arrives.
            ii = np.clip(np.floor(inv).astype(np.int64), 0, mmax)
            closure_projection = np.where(
                inv > 0.0,
                inv * cumprob[ii] - cumfirst[ii],
                0.0,
            )

            for j in range(L - 1):
                y = closure_projection + pipe[:, j]
                ii = np.clip(np.floor(y).astype(np.int64), 0, mmax)
                closure_projection = np.where(
                    y > 0.0,
                    y * cumprob[ii] - cumfirst[ii],
                    0.0,
                )

            if w < 0.999999:
                # A second projection propagates both mean and variance using
                # moment-matched positive-normal recursions.
                mm = inv.copy()
                vv = np.zeros(nrep, dtype=float)

                for j in range(L):
                    nn = mm - mean_d
                    ss = np.sqrt(vv + var_d)
                    aa = nn / ss
                    pp = ndtr(aa)
                    ph = np.exp(-0.5 * aa * aa) / math.sqrt(2.0 * math.pi)

                    e2 = (ss * ss + nn * nn) * pp + nn * ss * ph
                    mm = ss * ph + nn * pp
                    vv = np.maximum(0.0, e2 - mm * mm)

                    if j < L - 1:
                        mm += pipe[:, j]

                projected = w * closure_projection + (1.0 - w) * mm
            else:
                projected = closure_projection

            order = np.maximum(
                0.0,
                target - b * projected - c * pipe.mean(axis=1),
            )

            demand = 0.0 if t < L else demands[:, t - L]
            sold = np.minimum(inv, demand)
            inv -= sold

            if t >= L:
                total += float(
                    np.mean(hold * inv + penalty * (demand - sold))
                )

            if t < L + H - 1:
                inv += pipe[:, 0]
                pipe[:, :-1] = pipe[:, 1:]
                pipe[:, -1] = order

        return total

    service_fraction = penalty / (penalty + hold)
    heuristic_d = max(
        0.0, np.rint(mu + sigma * ndtri(service_fraction))
    )
    heuristic = np.array(
        [
            min(upper_a, max(0.1, heuristic_d / mean_d)),
            0.8,
            0.0,
            1.0,
        ],
        dtype=float,
    )
    candidates = [heuristic]

    flex_bounds = [
        (0.05, upper_a),
        (0.10, 2.0),
        (0.0, 0.65),
        (0.0, 1.0),
    ]

    try:
        result = differential_evolution(
            lambda z: evaluate(z, train_demands),
            flex_bounds,
            maxiter=7,
            popsize=5,
            tol=0.004,
            polish=False,
            seed=871,
            workers=1,
            updating="immediate",
        )
        z0 = np.asarray(result.x, dtype=float)
        candidates.append(z0)

        local = minimize(
            lambda z: evaluate(z, train_demands),
            z0,
            method="Nelder-Mead",
            options={
                "maxfev": 90,
                "xatol": 0.002,
                "fatol": 0.03,
                "adaptive": True,
            },
        )
        if np.isfinite(local.fun) and local.fun < 1.0e90:
            candidates.append(np.asarray(local.x, dtype=float))
    except Exception:
        pass

    # Also construct a simpler expected-projected-inventory policy.
    try:
        simple = differential_evolution(
            lambda ab: evaluate(
                (ab[0], ab[1], 0.0, 1.0), train_demands
            ),
            [(0.05, upper_a), (0.10, 2.0)],
            maxiter=5,
            popsize=5,
            tol=0.004,
            polish=False,
            seed=318,
            workers=1,
            updating="immediate",
        )
        candidates.append(
            np.array([simple.x[0], simple.x[1], 0.0, 1.0])
        )
    except Exception:
        pass

    # Refine the target level on a larger independent quasi-Monte Carlo set.
    fine_demands = make_demands(12, 8161)
    refined = []

    for z in candidates:
        z = np.asarray(z, dtype=float).copy()
        if not (
            0.0 <= z[1] <= 2.25
            and 0.0 <= z[2] <= 0.85
            and 0.0 <= z[3] <= 1.0
        ):
            continue

        try:
            target_result = minimize_scalar(
                lambda a: evaluate(
                    (a, z[1], z[2], z[3]), fine_demands
                ),
                bounds=(0.05, upper_a),
                method="bounded",
                options={"xatol": 0.0015, "maxiter": 24},
            )
            z[0] = target_result.x
        except Exception:
            pass

        refined.append((evaluate(z, fine_demands), z))

    # Constant-order policy is useful for some high-variability instances.
    try:
        constant_result = minimize_scalar(
            lambda a: evaluate(
                (a, 0.0, 0.0, 1.0), fine_demands
            ),
            bounds=(0.05, min(3.0, upper_a)),
            method="bounded",
            options={"xatol": 0.0015, "maxiter": 24},
        )
        constant_policy = np.array(
            [constant_result.x, 0.0, 0.0, 1.0]
        )
        refined.append(
            (
                evaluate(constant_policy, fine_demands),
                constant_policy,
            )
        )
    except Exception:
        pass

    best = (
        min(refined, key=lambda item: item[0])[1]
        if refined
        else heuristic
    )

    target = float(best[0] * mean_d)
    bcoef = float(best[1])
    ccoef = float(best[2])
    blend = float(best[3])

    root2pi = math.sqrt(2.0 * math.pi)
    root2 = math.sqrt(2.0)
    huge = max(
        1.0e12,
        1.0e9 * (target + L * mean_d + 1.0),
    )

    def expected_leftover(x):
        if x <= 0.0:
            return 0.0
        if x > huge:
            return x - mean_d

        k = int(math.floor(x))
        if k >= mmax:
            return (
                x * float(cumprob[-1]) - float(cumfirst[-1])
            )
        return x * float(cumprob[k]) - float(cumfirst[k])

    def compute_order_amount(on_hand_inventory, pipeline_orders):
        inv = float(on_hand_inventory)
        pipe = np.asarray(
            pipeline_orders, dtype=float
        ).reshape(-1)

        if inv > huge or (
            pipe.size and float(np.max(pipe)) > huge
        ):
            return 0.0

        if bcoef == 0.0 and ccoef == 0.0:
            return target

        closure_projection = expected_leftover(inv)
        for value in pipe:
            closure_projection = expected_leftover(
                closure_projection + float(value)
            )

        if blend < 0.999999:
            mm = inv
            vv = 0.0

            for j in range(L):
                nn = mm - mean_d
                ss = math.sqrt(vv + var_d)
                aa = nn / ss

                if aa >= 9.0:
                    mm = nn
                    vv = ss * ss
                elif aa <= -9.0:
                    mm = 0.0
                    vv = 0.0
                else:
                    pp = 0.5 * (
                        1.0 + math.erf(aa / root2)
                    )
                    ph = math.exp(-0.5 * aa * aa) / root2pi
                    e2 = (
                        (ss * ss + nn * nn) * pp
                        + nn * ss * ph
                    )
                    mm = ss * ph + nn * pp
                    vv = max(0.0, e2 - mm * mm)

                if j < L - 1:
                    mm += float(pipe[j])

            projected = (
                blend * closure_projection
                + (1.0 - blend) * mm
            )
        else:
            projected = closure_projection

        average_pipe = float(np.mean(pipe))
        ans = (
            target
            - bcoef * projected
            - ccoef * average_pipe
        )

        if ans <= 0.0 or not math.isfinite(ans):
            return 0.0
        return float(ans)

    return compute_order_amount
