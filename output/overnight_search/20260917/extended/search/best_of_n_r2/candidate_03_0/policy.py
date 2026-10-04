def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 15.0 # OPT_PARAM: {"type":"float","initial":15.0,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    W0 = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":2.0}
    W1 = 0.95 # OPT_PARAM: {"type":"float","initial":0.95,"min":0.0,"max":4.0}
    A = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":6.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    B = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.0,"max":1.0}
    D = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":3.0}

    m = len(age)
    state = [0.0] * m
    for i in range(m):
        x = float(age[i])
        if x < 0.0:
            x = 0.0
        state[i] = x

    for t in range(L):
        for stream in range(2):
            if stream == 0:
                g = f
            else:
                g = 1.0 - f

            if g > 0.0:
                M = g * mu
                V = g * (mu * cv) * (mu * cv)
                da = V / (M * M) - 1.0 / M
                disc = da * da - 1.0
                if disc < 0.0:
                    disc = 0.0
                root = disc ** 0.5
                db = 1.0 + da + root
                dc = 1.0 + da - root
                mix1 = 1.0 / db
                p1 = 2.0 / (2.0 + M * db)
                p2 = 2.0 / (2.0 + M * dc)
                r1 = 1.0 - p1
                r2 = 1.0 - p2
                cumulative = 0.0

                for pos in range(m):
                    if stream == 0:
                        i = pos
                    else:
                        i = m - 1 - pos

                    stock = state[i]
                    upper = cumulative + stock
                    n0 = int(cumulative)
                    n1 = int(upper)
                    frac0 = cumulative - n0
                    frac1 = upper - n1

                    e0r1 = r1 * (1.0 - r1 ** n0) / (1.0 - r1)
                    e0r1 = e0r1 + frac0 * r1 ** (n0 + 1)
                    e1r1 = r1 * (1.0 - r1 ** n1) / (1.0 - r1)
                    e1r1 = e1r1 + frac1 * r1 ** (n1 + 1)

                    e0r2 = r2 * (1.0 - r2 ** n0) / (1.0 - r2)
                    e0r2 = e0r2 + frac0 * r2 ** (n0 + 1)
                    e1r2 = r2 * (1.0 - r2 ** n1) / (1.0 - r2)
                    e1r2 = e1r2 + frac1 * r2 ** (n1 + 1)

                    h0 = mix1 * e0r1 + (1.0 - mix1) * e0r2
                    h1 = mix1 * e1r1 + (1.0 - mix1) * e1r2
                    consumed = D * (h1 - h0)
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > stock:
                        consumed = stock

                    state[i] = stock - consumed
                    cumulative = upper

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = state[i + 1]
        shifted[m - 1] = 0.0
        state = shifted

        if t < L - 1 and t < len(pipeline):
            incoming = float(pipeline[t])
            if incoming > 0.0:
                state[m - 1] = state[m - 1] + incoming

    projected_credit = 0.0
    static_credit = 0.0
    for i in range(m):
        life_fraction = (i + 1.0) / m
        weight = W0 + W1 * life_fraction ** A
        projected_credit = projected_credit + weight * state[i]

        current_stock = float(age[i])
        if current_stock < 0.0:
            current_stock = 0.0
        static_credit = static_credit + weight * current_stock

    pipeline_stock = 0.0
    for j in range(len(pipeline)):
        x = float(pipeline[j])
        if x > 0.0:
            pipeline_stock = pipeline_stock + x
    static_credit = static_credit + P * pipeline_stock

    effective = B * projected_credit + (1.0 - B) * static_credit
    raw = S - effective
    if raw != raw:
        return 0.0
    if raw < 0.0:
        return 0.0
    if raw > C:
        return C
    return raw
