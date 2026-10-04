def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    K_LATE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":6.0}
    FRESH_FLOOR = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    TAIL = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value >= 0.0:
            x[i] = value
        else:
            x[i] = 0.0

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            arrival = float(pipeline[t - 1])
            if not (arrival >= 0.0):
                arrival = 0.0
            x[m - 1] = x[m - 1] + arrival

        if t == 0:
            period_scale = K
        else:
            period_scale = K * K_LATE

        for group_index in range(2):
            if group_index == 0:
                g = f
            else:
                g = 1.0 - f

            M = g * mu
            if M > 0.0:
                V = g * (mu * cv) * (mu * cv)
                aa = V / (M * M) - 1.0 / M
                if aa < 1.0:
                    aa = 1.0

                root = (aa * aa - 1.0) ** 0.5
                b = 1.0 + aa + root
                c = 1.0 + aa - root
                weight1 = 1.0 / b
                p1 = 2.0 / (2.0 + M * b)
                p2 = 2.0 / (2.0 + M * c)
                r1 = 1.0 - p1
                r2 = 1.0 - p2

                cumulative = 0.0
                for step in range(m):
                    if group_index == 0:
                        idx = step
                    else:
                        idx = m - 1 - step

                    layer = x[idx]
                    lower = cumulative
                    upper = cumulative + layer

                    n0 = int(lower)
                    frac0 = lower - n0
                    if n0 > 0:
                        h10 = r1 * (1.0 - r1 ** n0) / p1
                        h20 = r2 * (1.0 - r2 ** n0) / p2
                    else:
                        h10 = 0.0
                        h20 = 0.0
                    expected0 = (
                        weight1 * (h10 + frac0 * r1 ** (n0 + 1))
                        + (1.0 - weight1) * (h20 + frac0 * r2 ** (n0 + 1))
                    )

                    n1 = int(upper)
                    frac1 = upper - n1
                    if n1 > 0:
                        h11 = r1 * (1.0 - r1 ** n1) / p1
                        h21 = r2 * (1.0 - r2 ** n1) / p2
                    else:
                        h11 = 0.0
                        h21 = 0.0
                    expected1 = (
                        weight1 * (h11 + frac1 * r1 ** (n1 + 1))
                        + (1.0 - weight1) * (h21 + frac1 * r2 ** (n1 + 1))
                    )

                    depletion = period_scale * (expected1 - expected0)
                    if depletion < 0.0:
                        depletion = 0.0
                    if depletion > layer:
                        depletion = layer

                    x[idx] = layer - depletion
                    cumulative = upper

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0

    effective = 0.0
    for i in range(m):
        freshness = (i + 1.0) / m
        weight = FRESH_FLOOR + (1.0 - FRESH_FLOOR) * freshness ** A
        effective = effective + weight * x[i]

    gap = S - effective
    if gap <= 0.0:
        return 0.0
    if gap <= C:
        q = gap
    else:
        q = C + TAIL * (gap - C)

    if not (q >= 0.0):
        q = 0.0
    return float(q)
