def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":30.0}
    B0 = 1.1 # OPT_PARAM: {"type":"float","initial":1.1,"min":0.0,"max":3.5}
    B1 = -0.5 # OPT_PARAM: {"type":"float","initial":-0.5,"min":-4.0,"max":4.0}
    B2 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-4.0,"max":4.0}
    H0 = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":-3.0,"max":5.0}
    H1 = -0.25 # OPT_PARAM: {"type":"float","initial":-0.25,"min":-4.0,"max":5.0}
    H2 = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":-4.0,"max":5.0}
    DF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}
    DY = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}

    m = len(age)
    stock = [0.0] * m
    for i in range(m):
        stock[i] = age[i]

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
            root_value = aa * aa - 1.0
            if root_value < 0.0:
                root_value = 0.0
            root = root_value ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            mix[s] = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1[s] = 1.0 - p1
            r2[s] = 1.0 - p2

    for t in range(L):
        for s in range(2):
            if means[s] > 0.0:
                cumulative = 0.0
                expected_before = 0.0
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
                    cumulative = cumulative_new
                    expected_before = expected_after

        for i in range(m - 1):
            stock[i] = stock[i + 1]
        stock[m - 1] = 0.0
        if t < len(pipeline):
            stock[m - 1] = pipeline[t]

    projected_total = 0.0
    projected_old = 0.0
    projected_short = 0.0
    for i in range(m):
        x = stock[i]
        projected_total = projected_total + x
        if m > 1:
            oldness = (m - 1.0 - i) / (m - 1.0)
        else:
            oldness = 0.0
        projected_old = projected_old + oldness * x
        if i < L:
            projected_short = projected_short + x

    no_demand_total = 0.0
    no_demand_old = 0.0
    no_demand_short = 0.0

    for i in range(L, m):
        destination = i - L
        x = age[i]
        no_demand_total = no_demand_total + x
        if m > 1:
            oldness = (m - 1.0 - destination) / (m - 1.0)
        else:
            oldness = 0.0
        no_demand_old = no_demand_old + oldness * x
        if destination < L:
            no_demand_short = no_demand_short + x

    for j in range(len(pipeline)):
        destination = m - L + j
        if destination >= 0 and destination < m:
            x = pipeline[j]
            no_demand_total = no_demand_total + x
            if m > 1:
                oldness = (m - 1.0 - destination) / (m - 1.0)
            else:
                oldness = 0.0
            no_demand_old = no_demand_old + oldness * x
            if destination < L:
                no_demand_short = no_demand_short + x

    gap_total = no_demand_total - projected_total
    gap_old = no_demand_old - projected_old
    gap_short = no_demand_short - projected_short

    order = (
        S
        - B0 * projected_total
        - B1 * projected_old
        - B2 * projected_short
        - H0 * gap_total
        - H1 * gap_old
        - H2 * gap_short
    )
    if order < 0.0:
        order = 0.0
    if order > C:
        order = C
    return order
