def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":6.0}
    FRESH_FLOOR = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        x[i] = max(0.0, float(age[i]))

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + max(0.0, float(pipeline[t - 1]))

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
                w1 = 1.0 / b
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
                    z_values = [cumulative, cumulative + layer]
                    h_values = [0.0, 0.0]

                    for u in range(2):
                        z = z_values[u]
                        n = int(z)
                        frac = z - n

                        if n > 0:
                            h1 = r1 * (1.0 - r1 ** n) / p1
                            h2 = r2 * (1.0 - r2 ** n) / p2
                        else:
                            h1 = 0.0
                            h2 = 0.0

                        tail1 = r1 ** (n + 1)
                        tail2 = r2 ** (n + 1)
                        h_values[u] = (
                            w1 * (h1 + frac * tail1)
                            + (1.0 - w1) * (h2 + frac * tail2)
                        )

                    depletion = K * (h_values[1] - h_values[0])
                    if depletion < 0.0:
                        depletion = 0.0
                    if depletion > layer:
                        depletion = layer
                    x[idx] = layer - depletion
                    cumulative = z_values[1]

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0

    effective = 0.0
    for i in range(m):
        freshness = (i + 1.0) / m
        weight = FRESH_FLOOR + (1.0 - FRESH_FLOOR) * freshness ** A
        effective = effective + weight * x[i]

    q = S - effective
    if q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return float(q)
