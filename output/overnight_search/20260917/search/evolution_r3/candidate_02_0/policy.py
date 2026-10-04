def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    K_LATE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":6.0}
    FRESH_FLOOR = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    TAIL = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    MARGINAL_BLEND = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}

    m = len(age)
    x = [0.0] * m

    for i in range(m):
        value = float(age[i])
        if not (value >= 0.0):
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        x[i] = value

    active = [False, False]
    p1_values = [1.0, 1.0]
    p2_values = [1.0, 1.0]
    r1_values = [0.0, 0.0]
    r2_values = [0.0, 0.0]
    w1_values = [0.0, 0.0]

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
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)

            active[group_index] = True
            p1_values[group_index] = p1
            p2_values[group_index] = p2
            r1_values[group_index] = 1.0 - p1
            r2_values[group_index] = 1.0 - p2
            w1_values[group_index] = 1.0 / b

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            arrival = float(pipeline[t - 1])
            if not (arrival >= 0.0):
                arrival = 0.0
            if arrival > 1000000.0:
                arrival = 1000000.0
            x[m - 1] = x[m - 1] + arrival

        if t == 0:
            period_scale = K
        else:
            period_scale = K * K_LATE

        for group_index in range(2):
            if active[group_index]:
                p1 = p1_values[group_index]
                p2 = p2_values[group_index]
                r1 = r1_values[group_index]
                r2 = r2_values[group_index]
                w1 = w1_values[group_index]
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
                        w1 * (h10 + frac0 * r1 ** (n0 + 1))
                        + (1.0 - w1) * (h20 + frac0 * r2 ** (n0 + 1))
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
                        w1 * (h11 + frac1 * r1 ** (n1 + 1))
                        + (1.0 - w1) * (h21 + frac1 * r2 ** (n1 + 1))
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

    weighted_inventory = 0.0
    for i in range(m):
        freshness = (i + 1.0) / m
        weight = FRESH_FLOOR + (1.0 - FRESH_FLOOR) * freshness ** A
        weighted_inventory = weighted_inventory + weight * x[i]

    probe_gap = S - weighted_inventory
    if probe_gap <= 0.0:
        probe_order = 0.0
    elif probe_gap <= C:
        probe_order = probe_gap
    else:
        probe_order = C + TAIL * (probe_gap - C)

    y = [0.0] * m
    old = [0.0] * m
    for i in range(m):
        y[i] = x[i]
        old[i] = x[i]

    credited_sales = 0.0

    for t in range(m):
        if t == 0:
            future_arrival = probe_order
        else:
            future_arrival = mu

        if future_arrival < 0.0:
            future_arrival = 0.0
        y[m - 1] = y[m - 1] + future_arrival

        for group_index in range(2):
            if active[group_index]:
                p1 = p1_values[group_index]
                p2 = p2_values[group_index]
                r1 = r1_values[group_index]
                r2 = r2_values[group_index]
                w1 = w1_values[group_index]
                cumulative = 0.0

                for step in range(m):
                    if group_index == 0:
                        idx = step
                    else:
                        idx = m - 1 - step

                    layer = y[idx]
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
                        w1 * (h10 + frac0 * r1 ** (n0 + 1))
                        + (1.0 - w1) * (h20 + frac0 * r2 ** (n0 + 1))
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
                        w1 * (h11 + frac1 * r1 ** (n1 + 1))
                        + (1.0 - w1) * (h21 + frac1 * r2 ** (n1 + 1))
                    )

                    depletion = K * (expected1 - expected0)
                    if depletion < 0.0:
                        depletion = 0.0
                    if depletion > layer:
                        depletion = layer

                    old_layer = old[idx]
                    if layer > 0.0 and old_layer > 0.0:
                        old_depletion = depletion * old_layer / layer
                        if old_depletion > old_layer:
                            old_depletion = old_layer
                    else:
                        old_depletion = 0.0

                    credited_sales = credited_sales + old_depletion
                    old[idx] = old_layer - old_depletion
                    y[idx] = layer - depletion
                    cumulative = upper

        for i in range(m - 1):
            y[i] = y[i + 1]
            old[i] = old[i + 1]
        y[m - 1] = 0.0
        old[m - 1] = 0.0

    effective = (
        (1.0 - MARGINAL_BLEND) * weighted_inventory
        + MARGINAL_BLEND * credited_sales
    )

    gap = S - effective
    if gap <= 0.0:
        q = 0.0
    elif gap <= C:
        q = gap
    else:
        q = C + TAIL * (gap - C)

    if not (q >= 0.0):
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
