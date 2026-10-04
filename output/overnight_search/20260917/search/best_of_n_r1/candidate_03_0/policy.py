def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    STOCH_MIX = 0.85 # OPT_PARAM: {"type":"float","initial":0.85,"min":0.0,"max":1.0}
    W_NEW = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    W_OLD = 1.3 # OPT_PARAM: {"type":"float","initial":1.3,"min":0.0,"max":3.0}
    AGE_POWER = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":4.0}

    m = len(age)
    work = [0.0 for i in range(m)]
    for i in range(m):
        x = float(age[i])
        if x > 0.0 and x < 1000000000000.0:
            work[i] = x

    demand_scale = float(mu) * float(cv)
    means = [float(f) * float(mu), (1.0 - float(f)) * float(mu)]
    variances = [
        float(f) * demand_scale * demand_scale,
        (1.0 - float(f)) * demand_scale * demand_scale
    ]

    p1 = [1.0, 1.0]
    p2 = [1.0, 1.0]
    mix1 = [1.0, 1.0]

    for sidx in range(2):
        M = means[sidx]
        V = variances[sidx]
        if M > 0.0:
            a = V / (M * M) - 1.0 / M
            if a < 1.0:
                a = 1.0
            root = (a * a - 1.0) ** 0.5
            b = 1.0 + a + root
            c = 1.0 + a - root
            mix1[sidx] = 1.0 / b
            p1[sidx] = 2.0 / (2.0 + M * b)
            p2[sidx] = 2.0 / (2.0 + M * c)

    horizon = int(L)
    if horizon < 0:
        horizon = 0

    for t in range(horizon):
        if t > 0 and t - 1 < len(pipeline) and m > 0:
            arrival = float(pipeline[t - 1])
            if arrival > 0.0 and arrival < 1000000000000.0:
                work[m - 1] = work[m - 1] + arrival

        for sidx in range(2):
            M = means[sidx]
            if M > 0.0:
                r1 = 1.0 - p1[sidx]
                r2 = 1.0 - p2[sidx]
                w1 = mix1[sidx]
                w2 = 1.0 - w1
                cumulative = 0.0

                for k in range(m):
                    if sidx == 0:
                        i = k
                    else:
                        i = m - 1 - k

                    stock = work[i]
                    upper = cumulative + stock

                    e_lower = (
                        w1 * r1 * (1.0 - r1 ** cumulative) / p1[sidx]
                        + w2 * r2 * (1.0 - r2 ** cumulative) / p2[sidx]
                    )
                    e_upper = (
                        w1 * r1 * (1.0 - r1 ** upper) / p1[sidx]
                        + w2 * r2 * (1.0 - r2 ** upper) / p2[sidx]
                    )

                    if cumulative < M:
                        fluid_lower = cumulative
                    else:
                        fluid_lower = M
                    if upper < M:
                        fluid_upper = upper
                    else:
                        fluid_upper = M

                    blended_lower = (
                        STOCH_MIX * e_lower
                        + (1.0 - STOCH_MIX) * fluid_lower
                    )
                    blended_upper = (
                        STOCH_MIX * e_upper
                        + (1.0 - STOCH_MIX) * fluid_upper
                    )
                    used = blended_upper - blended_lower

                    if used < 0.0:
                        used = 0.0
                    if used > stock:
                        used = stock

                    work[i] = stock - used
                    cumulative = upper

        shifted = [0.0 for i in range(m)]
        for i in range(m - 1):
            shifted[i] = work[i + 1]
        work = shifted

    effective_inventory = 0.0
    if m <= 1:
        if m == 1:
            effective_inventory = W_NEW * work[0]
    else:
        denominator = float(m - 1)
        for i in range(m):
            shortness = float(m - 1 - i) / denominator
            weight = W_NEW + (W_OLD - W_NEW) * (shortness ** AGE_POWER)
            if weight < 0.0:
                weight = 0.0
            effective_inventory = effective_inventory + weight * work[i]

    order = S - effective_inventory
    if not (order == order):
        return 0.0
    if order <= 0.0:
        return 0.0
    if order > 1000000.0:
        return 1000000.0
    return float(order)
