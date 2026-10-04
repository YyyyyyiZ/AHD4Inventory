def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":30.0}
    B0 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    B1 = -0.5 # OPT_PARAM: {"type":"float","initial":-0.5,"min":-5.0,"max":5.0}
    B2 = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-5.0,"max":5.0}
    B3 = -0.3 # OPT_PARAM: {"type":"float","initial":-0.3,"min":-5.0,"max":5.0}
    H = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-4.0,"max":5.0}
    Z = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":-1.5,"max":2.5}
    U = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-3.0,"max":6.0}
    W = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-4.0,"max":6.0}
    V = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":-5.0,"max":5.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":-8.0,"max":12.0}
    DF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":3.0}
    DY = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":3.0}

    m = len(age)
    if m <= 0:
        return 0.0

    nq = 9
    groups = [f, 1.0 - f]
    means = [f * mu, (1.0 - f) * mu]
    scales = [DF, DY]
    quantiles = [[0.0] * nq, [0.0] * nq]

    for s in range(2):
        M = means[s]
        if M > 0.0:
            Vd = groups[s] * (mu * cv) ** 2
            aa = Vd / (M * M) - 1.0 / M
            if aa < 1.0:
                aa = 1.0
            root_term = aa * aa - 1.0
            if root_term < 0.0:
                root_term = 0.0
            root = root_term ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            mix = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1 = 1.0 - p1
            r2 = 1.0 - p2

            for r in range(nq):
                quantiles[s][r] = -1.0

            for k in range(161):
                survival = mix * r1 ** (k + 1.0) + (1.0 - mix) * r2 ** (k + 1.0)
                cdf = 1.0 - survival
                for r in range(nq):
                    target = (r + 0.5) / nq
                    if quantiles[s][r] < 0.0 and cdf >= target:
                        quantiles[s][r] = float(k)

            for r in range(nq):
                if quantiles[s][r] < 0.0:
                    quantiles[s][r] = 161.0

    map_fifo_0 = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    map_lifo_0 = [8, 7, 0, 1, 2, 3, 6, 4, 5]
    map_fifo_1 = [6, 0, 8, 1, 2, 3, 4, 7, 5]
    map_lifo_1 = [6, 0, 1, 8, 2, 3, 4, 5, 7]

    weights = [0.0] * m
    for i in range(m):
        if m > 1:
            oldness = (m - 1.0 - i) / (m - 1.0)
        else:
            oldness = 0.0
        short_flag = 0.0
        if i < L:
            short_flag = 1.0
        weights[i] = B0 + B1 * oldness + B2 * oldness * oldness + B3 * short_flag

    scenario_effective = [0.0] * nq
    mean_effective = 0.0
    mean_total = 0.0
    mean_total_square = 0.0
    mean_lost = 0.0
    mean_expired = 0.0
    empty_probability = 0.0

    for r in range(nq):
        stock = [0.0] * m
        for i in range(m):
            x = age[i]
            if x < 0.0:
                x = 0.0
            stock[i] = x

        scenario_lost = 0.0
        scenario_expired = 0.0

        for t in range(L):
            if t == 0:
                fifo_index = map_fifo_0[r]
                lifo_index = map_lifo_0[r]
            else:
                fifo_index = map_fifo_1[r]
                lifo_index = map_lifo_1[r]

            fifo_demand = scales[0] * quantiles[0][fifo_index]
            lifo_demand = scales[1] * quantiles[1][lifo_index]

            remaining = fifo_demand
            for i in range(m):
                x = stock[i]
                used = remaining
                if used > x:
                    used = x
                if used < 0.0:
                    used = 0.0
                stock[i] = x - used
                remaining = remaining - used
            if remaining > 0.0:
                scenario_lost = scenario_lost + remaining

            remaining = lifo_demand
            for k in range(m):
                i = m - 1 - k
                x = stock[i]
                used = remaining
                if used > x:
                    used = x
                if used < 0.0:
                    used = 0.0
                stock[i] = x - used
                remaining = remaining - used
            if remaining > 0.0:
                scenario_lost = scenario_lost + remaining

            scenario_expired = scenario_expired + stock[0]
            for i in range(m - 1):
                stock[i] = stock[i + 1]
            stock[m - 1] = 0.0
            if t < len(pipeline):
                x = pipeline[t]
                if x < 0.0:
                    x = 0.0
                stock[m - 1] = x

        total = 0.0
        effective = 0.0
        for i in range(m):
            total = total + stock[i]
            effective = effective + weights[i] * stock[i]

        scenario_effective[r] = effective
        mean_effective = mean_effective + effective / nq
        mean_total = mean_total + total / nq
        mean_total_square = mean_total_square + total * total / nq
        mean_lost = mean_lost + scenario_lost / nq
        mean_expired = mean_expired + scenario_expired / nq
        if total < 0.5:
            empty_probability = empty_probability + 1.0 / nq

    ordered_effective = [0.0] * nq
    for i in range(nq):
        ordered_effective[i] = scenario_effective[i]

    for i in range(nq - 1):
        for j in range(nq - 1 - i):
            if ordered_effective[j] > ordered_effective[j + 1]:
                temp = ordered_effective[j]
                ordered_effective[j] = ordered_effective[j + 1]
                ordered_effective[j + 1] = temp

    median_effective = ordered_effective[nq // 2]
    selected_effective = mean_effective + Z * (median_effective - mean_effective)

    no_demand_effective = 0.0
    for i in range(L, m):
        x = age[i]
        if x < 0.0:
            x = 0.0
        no_demand_effective = no_demand_effective + weights[i - L] * x

    for j in range(len(pipeline)):
        destination = m - L + j
        if destination >= 0 and destination < m:
            x = pipeline[j]
            if x < 0.0:
                x = 0.0
            no_demand_effective = no_demand_effective + weights[destination] * x

    variance_total = mean_total_square - mean_total * mean_total
    if variance_total < 0.0:
        variance_total = 0.0
    standard_deviation = variance_total ** 0.5
    lead_gap = no_demand_effective - mean_effective

    order = (
        S
        - selected_effective
        - H * lead_gap
        + U * mean_lost
        - W * mean_expired
        + V * standard_deviation
        + G * empty_probability
    )

    if order != order:
        return 0.0
    if order < 0.0:
        order = 0.0
    if order > C:
        order = C
    if order > 1.0e100:
        order = C
    return order
