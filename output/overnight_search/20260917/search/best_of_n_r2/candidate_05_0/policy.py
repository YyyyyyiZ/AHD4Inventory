def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":2.5}
    D_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.5,"max":1.5}
    W_OLD = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":3.0}
    W_SLOPE = 0.4 # OPT_PARAM: {"type":"float","initial":0.4,"min":-3.0,"max":3.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        v = float(age[i])
        if v != v or v < 0.0:
            v = 0.0
        if v > 1000000.0:
            v = 1000000.0
        x[i] = v

    horizon = int(L)
    for step in range(horizon):
        for group in range(2):
            if group == 0:
                g = float(f)
            else:
                g = 1.0 - float(f)

            if g > 0.0:
                M = g * float(mu)
                V = g * (float(mu) * float(cv)) ** 2
                a = V / (M * M) - 1.0 / M
                root = (a * a - 1.0) ** 0.5
                b = 1.0 + a + root
                c = 1.0 + a - root
                mix = 1.0 / b
                p1 = 2.0 / (2.0 + M * b)
                p2 = 2.0 / (2.0 + M * c)
                r1 = 1.0 - p1
                r2 = 1.0 - p2

                cumulative = 0.0
                previous_expected = 0.0
                for j in range(m):
                    if group == 0:
                        k = j
                    else:
                        k = m - 1 - j

                    cohort = x[k]
                    cumulative = cumulative + cohort
                    scaled_capacity = cumulative / D_SCALE
                    e1 = r1 * (1.0 - r1 ** scaled_capacity) / p1
                    e2 = r2 * (1.0 - r2 ** scaled_capacity) / p2
                    expected_used = D_SCALE * (mix * e1 + (1.0 - mix) * e2)
                    take = expected_used - previous_expected
                    if take < 0.0:
                        take = 0.0
                    if take > cohort:
                        take = cohort
                    x[k] = cohort - take
                    previous_expected = expected_used

        shifted = [0.0] * m
        for i in range(1, m):
            shifted[i - 1] = x[i]

        arrival = 0.0
        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival != arrival or arrival < 0.0:
                arrival = 0.0
            if arrival > 1000000.0:
                arrival = 1000000.0
        if m > 0:
            shifted[m - 1] = arrival
        x = shifted

    effective_inventory = 0.0
    for i in range(m):
        if m > 1:
            relative_age = float(i) / float(m - 1)
        else:
            relative_age = 0.0
        weight = W_OLD + W_SLOPE * relative_age
        if weight < 0.0:
            weight = 0.0
        if weight > 3.0:
            weight = 3.0
        effective_inventory = effective_inventory + weight * x[i]

    order = GAIN * (S - effective_inventory)
    if order != order or order <= 0.0:
        return 0.0
    if order > 1000000.0:
        return 1000000.0
    return float(order)
