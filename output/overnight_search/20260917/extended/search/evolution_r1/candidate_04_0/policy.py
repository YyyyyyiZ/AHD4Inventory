def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":30.0}
    B0 = 1.05 # OPT_PARAM: {"type":"float","initial":1.05,"min":0.0,"max":3.5}
    B1 = -0.1 # OPT_PARAM: {"type":"float","initial":-0.1,"min":-6.0,"max":6.0}
    B2 = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":-6.0,"max":6.0}
    BQ = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-6.0,"max":6.0}
    BF = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-6.0,"max":6.0}
    BC = -0.15 # OPT_PARAM: {"type":"float","initial":-0.15,"min":-4.0,"max":4.0}
    H0 = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":-3.0,"max":5.0}
    H1 = -0.2 # OPT_PARAM: {"type":"float","initial":-0.2,"min":-6.0,"max":6.0}
    H2 = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":-6.0,"max":6.0}
    HC = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-4.0,"max":4.0}
    DF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}
    DY = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}

    m = len(age)
    if m <= 0:
        return 0.0

    stock = [0.0] * m
    for i in range(m):
        x = age[i]
        if x != x or x < 0.0:
            x = 0.0
        stock[i] = x

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
            x = pipeline[t]
            if x != x or x < 0.0:
                x = 0.0
            stock[m - 1] = x

    projected_total = 0.0
    projected_old = 0.0
    projected_old_square = 0.0
    projected_short = 0.0
    projected_fresh = 0.0
    projected_square_sum = 0.0

    for i in range(m):
        x = stock[i]
        if m > 1:
            oldness = (m - 1.0 - i) / (m - 1.0)
        else:
            oldness = 0.0
        projected_total = projected_total + x
        projected_old = projected_old + oldness * x
        projected_old_square = projected_old_square + oldness * oldness * x
        projected_square_sum = projected_square_sum + x * x
        if i < L:
            projected_short = projected_short + x
        if i >= m - L:
            projected_fresh = projected_fresh + x

    projected_concentration = projected_square_sum / (1.0 + projected_total)

    no_demand_total = 0.0
    no_demand_old = 0.0
    no_demand_short = 0.0
    no_demand_square_sum = 0.0
    no_demand_stock = [0.0] * m

    for i in range(L, m):
        destination = i - L
        x = age[i]
        if x != x or x < 0.0:
            x = 0.0
        no_demand_stock[destination] = no_demand_stock[destination] + x

    for j in range(len(pipeline)):
        destination = m - L + j
        if destination >= 0 and destination < m:
            x = pipeline[j]
            if x != x or x < 0.0:
                x = 0.0
            no_demand_stock[destination] = no_demand_stock[destination] + x

    for i in range(m):
        x = no_demand_stock[i]
        if m > 1:
            oldness = (m - 1.0 - i) / (m - 1.0)
        else:
            oldness = 0.0
        no_demand_total = no_demand_total + x
        no_demand_old = no_demand_old + oldness * x
        no_demand_square_sum = no_demand_square_sum + x * x
        if i < L:
            no_demand_short = no_demand_short + x

    no_demand_concentration = no_demand_square_sum / (1.0 + no_demand_total)

    gap_total = no_demand_total - projected_total
    gap_old = no_demand_old - projected_old
    gap_short = no_demand_short - projected_short
    gap_concentration = no_demand_concentration - projected_concentration

    order = (
        S
        - B0 * projected_total
        - B1 * projected_old
        - B2 * projected_short
        - BQ * projected_old_square
        - BF * projected_fresh
        - BC * projected_concentration
        - H0 * gap_total
        - H1 * gap_old
        - H2 * gap_short
        - HC * gap_concentration
    )

    if order != order:
        return 0.0
    if order < 0.0:
        order = 0.0
    if order > C:
        order = C
    return order
