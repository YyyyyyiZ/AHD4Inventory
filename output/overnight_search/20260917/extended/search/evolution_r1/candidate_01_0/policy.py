def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 13.0 # OPT_PARAM: {"type":"float","initial":13.0,"min":0.0,"max":60.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":30.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.5}
    H = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":-2.0,"max":3.0}
    A = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":4.0}
    R = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    DF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}
    DY = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}

    m = len(age)
    weights = [0.0] * m
    for i in range(m):
        weight = ((i + 1.0) / m) ** A
        if i < L:
            weight = weight * R
        weights[i] = weight

    groups = [f, 1.0 - f]
    means = [f * mu, (1.0 - f) * mu]
    scales = [DF, DY]
    mix = [0.0, 0.0]
    r1 = [0.0, 0.0]
    r2 = [0.0, 0.0]

    for s in range(2):
        M = means[s]
        if M > 0.0:
            V = groups[s] * (mu * cv) ** 2
            aa = V / (M * M) - 1.0 / M
            root_term = aa * aa - 1.0
            if root_term < 0.0:
                root_term = 0.0
            root = root_term ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            w = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            mix[s] = w
            r1[s] = 1.0 - p1
            r2[s] = 1.0 - p2

    stock = [0.0] * m
    for i in range(m):
        stock[i] = age[i]

    for t in range(L):
        for s in range(2):
            if means[s] > 0.0:
                cumulative = 0.0
                expected_before = 0.0
                scale = scales[s]
                w = mix[s]
                one_minus_w = 1.0 - w
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
                        + one_minus_w * rr2 * (1.0 - rr2 ** z) / denom2
                    )
                    used = expected_after - expected_before
                    if used < 0.0:
                        used = 0.0
                    if used > x:
                        used = x
                    stock[idx] = x - used
                    cumulative = cumulative_new
                    expected_before = expected_after

        for i in range(m - 1):
            stock[i] = stock[i + 1]
        stock[m - 1] = 0.0
        if t < len(pipeline):
            stock[m - 1] = stock[m - 1] + pipeline[t]

    expected_effective = 0.0
    for i in range(m):
        expected_effective = expected_effective + weights[i] * stock[i]

    no_demand_effective = 0.0
    for i in range(L, m):
        no_demand_effective = no_demand_effective + weights[i - L] * age[i]
    for j in range(len(pipeline)):
        destination = m - L + j
        if destination >= 0 and destination < m:
            no_demand_effective = no_demand_effective + weights[destination] * pipeline[j]

    uncertainty_gap = no_demand_effective - expected_effective
    order = S - K * expected_effective - H * uncertainty_gap
    return max(0.0, min(C, order))
