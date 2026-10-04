def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    C = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":30.0}
    B0 = 1.4 # OPT_PARAM: {"type":"float","initial":1.4,"min":-3.0,"max":6.0}
    B1 = 1.1 # OPT_PARAM: {"type":"float","initial":1.1,"min":-3.0,"max":6.0}
    B2 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":-3.0,"max":6.0}
    B3 = 1.1 # OPT_PARAM: {"type":"float","initial":1.1,"min":-3.0,"max":6.0}
    H0 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-4.0,"max":6.0}
    H1 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-4.0,"max":6.0}
    H2 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-4.0,"max":6.0}
    H3 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-4.0,"max":6.0}
    DF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.6,"max":3.0}
    DY = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.3,"max":3.0}
    Q = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":3.0}

    m = len(age)
    if m == 0:
        return 0.0

    stock = [0.0] * m
    for i in range(m):
        value = age[i]
        if value < 0.0:
            value = 0.0
        stock[i] = value

    means = [f * mu, (1.0 - f) * mu]
    groups = [f, 1.0 - f]
    mix = [0.0, 0.0]
    pzero1 = [1.0, 1.0]
    pzero2 = [1.0, 1.0]
    ratio1 = [0.0, 0.0]
    ratio2 = [0.0, 0.0]

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
            pzero1[s] = p1
            pzero2[s] = p2
            ratio1[s] = 1.0 - p1
            ratio2[s] = 1.0 - p2

    for t in range(L):
        total = 0.0
        for i in range(m):
            total = total + stock[i]

        expected_stock = [0.0] * m
        fifo_mean = means[0]

        for d in range(97):
            if fifo_mean > 0.0:
                fifo_take = DF * d
                if d > 0 and fifo_take >= total:
                    break
                w_fifo = mix[0]
                probability = (
                    w_fifo * pzero1[0] * ratio1[0] ** d
                    + (1.0 - w_fifo) * pzero2[0] * ratio2[0] ** d
                )
            else:
                if d > 0:
                    break
                fifo_take = 0.0
                probability = 1.0

            scenario = [0.0] * m
            remaining_fifo = fifo_take
            for i in range(m):
                x = stock[i]
                used = remaining_fifo
                if used > x:
                    used = x
                if used < 0.0:
                    used = 0.0
                scenario[i] = x - used
                remaining_fifo = remaining_fifo - used

            lifo_mean = means[1]
            if lifo_mean > 0.0:
                cumulative = 0.0
                expected_before = 0.0
                w_lifo = mix[1]
                rr1 = ratio1[1]
                rr2 = ratio2[1]
                denom1 = 1.0 - rr1
                denom2 = 1.0 - rr2

                for k in range(m):
                    idx = m - 1 - k
                    x = scenario[idx]
                    cumulative_new = cumulative + x
                    z = cumulative_new / DY
                    expected_after = DY * (
                        w_lifo * rr1 * (1.0 - rr1 ** z) / denom1
                        + (1.0 - w_lifo) * rr2 * (1.0 - rr2 ** z) / denom2
                    )
                    used = expected_after - expected_before
                    if used < 0.0:
                        used = 0.0
                    if used > x:
                        used = x
                    scenario[idx] = x - used
                    cumulative = cumulative_new
                    expected_before = expected_after

            for i in range(m):
                expected_stock[i] = expected_stock[i] + probability * scenario[i]

        for i in range(m - 1):
            stock[i] = expected_stock[i + 1]
        stock[m - 1] = 0.0
        if t < len(pipeline):
            arrival = pipeline[t]
            if arrival < 0.0:
                arrival = 0.0
            stock[m - 1] = arrival

    no_demand = [0.0] * m
    for i in range(m):
        destination = i - L
        if destination >= 0:
            value = age[i]
            if value < 0.0:
                value = 0.0
            no_demand[destination] = no_demand[destination] + value

    for j in range(len(pipeline)):
        destination = m - L + j
        if destination >= 0 and destination < m:
            value = pipeline[j]
            if value < 0.0:
                value = 0.0
            no_demand[destination] = no_demand[destination] + value

    projected_effective = 0.0
    depletion_effective = 0.0
    projected_total = 0.0

    for i in range(m):
        if m > 1:
            x = i / (m - 1.0)
        else:
            x = 1.0
        one_minus_x = 1.0 - x
        basis0 = one_minus_x ** 3
        basis1 = 3.0 * x * one_minus_x ** 2
        basis2 = 3.0 * x * x * one_minus_x
        basis3 = x ** 3
        projected_weight = (
            B0 * basis0
            + B1 * basis1
            + B2 * basis2
            + B3 * basis3
        )
        depletion_weight = (
            H0 * basis0
            + H1 * basis1
            + H2 * basis2
            + H3 * basis3
        )
        gap = no_demand[i] - stock[i]
        projected_effective = projected_effective + projected_weight * stock[i]
        depletion_effective = depletion_effective + depletion_weight * gap
        projected_total = projected_total + stock[i]

    scale = mu * m
    if scale <= 0.0:
        scale = 1.0

    order = (
        S
        - projected_effective
        - depletion_effective
        - Q * projected_total * projected_total / scale
    )

    if order != order:
        return 0.0
    if order <= 0.0:
        return 0.0
    if order >= C:
        return C
    return order
