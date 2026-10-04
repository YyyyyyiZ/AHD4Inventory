def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    C = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":30.0}
    B0 = 0.45 # OPT_PARAM: {"type":"float","initial":0.45,"min":0.0,"max":4.0}
    B1 = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":4.0}
    B2 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    B3 = 1.1 # OPT_PARAM: {"type":"float","initial":1.1,"min":0.0,"max":4.0}
    H0 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-2.0,"max":4.0}
    H1 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-2.0,"max":4.0}
    H2 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-2.0,"max":4.0}
    H3 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-2.0,"max":4.0}
    DF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":3.0}
    DY = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":3.0}
    U = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-1.0,"max":5.0}
    W = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-2.0,"max":5.0}
    LOW = 5.0 # OPT_PARAM: {"type":"float","initial":5.0,"min":0.0,"max":30.0}
    KL = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":-1.0,"max":4.0}

    m = len(age)
    stock = [0.0] * m
    no_demand = [0.0] * m

    for i in range(m):
        x = age[i]
        if x < 0.0:
            x = 0.0
        stock[i] = x

    means = [f * mu, (1.0 - f) * mu]
    groups = [f, 1.0 - f]
    scales = [DF, DY]
    mix = [0.0, 0.0]
    r1 = [0.0, 0.0]
    r2 = [0.0, 0.0]

    for s in range(2):
        M = means[s]
        if M > 0.0:
            V = groups[s] * (mu * cv) ** 2
            aa = V / (M * M) - 1.0 / M
            if aa < 1.0:
                aa = 1.0
            root_term = aa * aa - 1.0
            if root_term < 0.0:
                root_term = 0.0
            root = root_term ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            mix[s] = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1[s] = 1.0 - p1
            r2[s] = 1.0 - p2

    lead_lost = 0.0
    lead_expired = 0.0

    for t in range(L):
        for s in range(2):
            M = means[s]
            if M > 0.0:
                cumulative = 0.0
                expected_before = 0.0
                stream_used = 0.0
                scale = scales[s]
                w = mix[s]
                rr1 = r1[s]
                rr2 = r2[s]
                denom1 = 1.0 - rr1
                denom2 = 1.0 - rr2

                for k in range(m):
                    if s == 0:
                        idx = k
                    else:
                        idx = m - 1 - k

                    x = stock[idx]
                    cumulative_new = cumulative + x
                    z = cumulative_new / scale
                    expected_after = scale * (
                        w * rr1 * (1.0 - rr1 ** z) / denom1
                        + (1.0 - w) * rr2 * (1.0 - rr2 ** z) / denom2
                    )
                    used = expected_after - expected_before
                    if used < 0.0:
                        used = 0.0
                    if used > x:
                        used = x

                    stock[idx] = x - used
                    stream_used = stream_used + used
                    cumulative = cumulative_new
                    expected_before = expected_after

                if stream_used > M:
                    stream_used = M
                shortage = M - stream_used
                if shortage > 0.0:
                    lead_lost = lead_lost + shortage

        if m > 0:
            lead_expired = lead_expired + stock[0]

        for i in range(m - 1):
            stock[i] = stock[i + 1]

        if m > 0:
            stock[m - 1] = 0.0
            if t < len(pipeline):
                x = pipeline[t]
                if x < 0.0:
                    x = 0.0
                stock[m - 1] = x

    for i in range(L, m):
        x = age[i]
        if x < 0.0:
            x = 0.0
        no_demand[i - L] = no_demand[i - L] + x

    for j in range(len(pipeline)):
        destination = m - L + j
        if destination >= 0 and destination < m:
            x = pipeline[j]
            if x < 0.0:
                x = 0.0
            no_demand[destination] = no_demand[destination] + x

    projected_effective = 0.0
    uncertainty_effective = 0.0
    projected_total = 0.0

    for i in range(m):
        if m > 1:
            z = i / (m - 1.0)
        else:
            z = 1.0
        one = 1.0 - z
        b_weight = (
            B0 * one * one * one
            + 3.0 * B1 * one * one * z
            + 3.0 * B2 * one * z * z
            + B3 * z * z * z
        )
        h_weight = (
            H0 * one * one * one
            + 3.0 * H1 * one * one * z
            + 3.0 * H2 * one * z * z
            + H3 * z * z * z
        )
        x = stock[i]
        gap = no_demand[i] - x
        projected_effective = projected_effective + b_weight * x
        uncertainty_effective = uncertainty_effective + h_weight * gap
        projected_total = projected_total + x

    low_gap = LOW - projected_total
    if low_gap < 0.0:
        low_gap = 0.0

    order = (
        S
        - projected_effective
        - uncertainty_effective
        + U * lead_lost
        - W * lead_expired
        + KL * low_gap
    )

    if order != order:
        return 0.0
    if order < 0.0:
        order = 0.0
    if order > C:
        order = C
    return order
