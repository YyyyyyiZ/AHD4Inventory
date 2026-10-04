def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 11.0 # OPT_PARAM: {"type":"float","initial":11.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":2.0}
    D = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.5,"max":1.5}
    A = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.0}
    P = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.05,"max":6.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        x[i] = age[i]

    for t in range(L):
        for stream in range(2):
            if stream == 0:
                g = f
            else:
                g = 1.0 - f

            M = g * mu
            if M > 0.0:
                V = g * (mu * cv) * (mu * cv)
                ad = V / (M * M) - 1.0 / M
                disc = ad * ad - 1.0
                if disc < 0.0:
                    disc = 0.0
                root = disc ** 0.5
                b = 1.0 + ad + root
                c = 1.0 + ad - root
                w1 = 1.0 / b
                p1 = 2.0 / (2.0 + M * b)
                p2 = 2.0 / (2.0 + M * c)
                r1 = 1.0 - p1
                r2 = 1.0 - p2

                cumulative = 0.0
                previous = 0.0
                for k in range(m):
                    if stream == 0:
                        i = k
                    else:
                        i = m - 1 - k

                    xi = x[i]
                    cumulative = cumulative + xi
                    n = int(cumulative)
                    frac = cumulative - n

                    if n > 0:
                        e1 = r1 * (1.0 - r1 ** n) / (1.0 - r1)
                        e2 = r2 * (1.0 - r2 ** n) / (1.0 - r2)
                    else:
                        e1 = 0.0
                        e2 = 0.0

                    e1 = e1 + frac * (r1 ** (n + 1))
                    e2 = e2 + frac * (r2 ** (n + 1))
                    expected_cumulative = w1 * e1 + (1.0 - w1) * e2
                    removal = D * (expected_cumulative - previous)

                    if removal < 0.0:
                        removal = 0.0
                    if removal > xi:
                        removal = xi
                    x[i] = xi - removal
                    previous = expected_cumulative

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0
        if t < len(pipeline):
            x[m - 1] = pipeline[t]

    effective = 0.0
    for i in range(m):
        relative_life = (i + 1.0) / m
        weight = A + (1.0 - A) * (relative_life ** P)
        effective = effective + weight * x[i]

    gap = S - effective
    if gap > 0.0:
        q = K * gap
    else:
        q = 0.0

    if q > C:
        q = C
    if q < 0.0 or q != q:
        q = 0.0
    return q
