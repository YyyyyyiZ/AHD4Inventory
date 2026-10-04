def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":8.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    B = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":1.0}
    H = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":1.0}
    R = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":3.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}

    m = len(age)
    raw_effective = 0.0
    pipeline_stock = 0.0

    for i in range(m):
        stock = max(0.0, age[i])
        relative_life = (i + 1.0) / m
        raw_effective = raw_effective + stock * (relative_life ** A)

    for j in range(len(pipeline)):
        pipeline_stock = pipeline_stock + max(0.0, pipeline[j])

    raw_effective = raw_effective + P * pipeline_stock

    aggregate = [0.0] * m
    layered = [0.0] * m

    for i in range(m):
        stock = max(0.0, age[i])
        aggregate[i] = stock
        layered[i] = stock

    for step in range(L):
        for stream in range(2):
            if stream == 0:
                g = f
            else:
                g = 1.0 - f

            M = g * mu
            if M > 0.0:
                V = g * (mu * cv) * (mu * cv)
                shape = V / (M * M) - 1.0 / M
                root = max(0.0, shape * shape - 1.0) ** 0.5
                b = 1.0 + shape + root
                c = 1.0 + shape - root
                weight1 = 1.0 / b
                p1 = 2.0 / (2.0 + M * b)
                p2 = 2.0 / (2.0 + M * c)
                r1 = (1.0 - p1) ** R
                r2 = (1.0 - p2) ** R

                available = 0.0
                for i in range(m):
                    available = available + aggregate[i]

                expected_use = 0.0
                if available > 0.0:
                    n = int(available)
                    fraction = available - n

                    if n > 0:
                        use1 = r1 * (1.0 - r1 ** n) / max(1.0e-12, 1.0 - r1)
                        use2 = r2 * (1.0 - r2 ** n) / max(1.0e-12, 1.0 - r2)
                        expected_use = weight1 * use1 + (1.0 - weight1) * use2

                    tail = weight1 * (r1 ** (n + 1))
                    tail = tail + (1.0 - weight1) * (r2 ** (n + 1))
                    expected_use = expected_use + fraction * tail
                    expected_use = max(0.0, min(available, expected_use))

                remaining = expected_use
                if stream == 0:
                    for i in range(m):
                        take = min(aggregate[i], remaining)
                        aggregate[i] = aggregate[i] - take
                        remaining = remaining - take
                else:
                    for i in range(m - 1, -1, -1):
                        take = min(aggregate[i], remaining)
                        aggregate[i] = aggregate[i] - take
                        remaining = remaining - take

                cumulative = 0.0
                for pos in range(m):
                    if stream == 0:
                        idx = pos
                    else:
                        idx = m - 1 - pos

                    cohort = layered[idx]
                    lower = cumulative
                    upper = cumulative + cohort
                    lower_n = int(lower)
                    upper_n = int(upper)
                    lower_fraction = lower - lower_n
                    upper_fraction = upper - upper_n
                    lower_use = 0.0
                    upper_use = 0.0

                    if lower_n > 0:
                        use1 = r1 * (1.0 - r1 ** lower_n) / max(1.0e-12, 1.0 - r1)
                        use2 = r2 * (1.0 - r2 ** lower_n) / max(1.0e-12, 1.0 - r2)
                        lower_use = weight1 * use1 + (1.0 - weight1) * use2

                    lower_tail = weight1 * (r1 ** (lower_n + 1))
                    lower_tail = lower_tail + (1.0 - weight1) * (r2 ** (lower_n + 1))
                    lower_use = lower_use + lower_fraction * lower_tail

                    if upper_n > 0:
                        use1 = r1 * (1.0 - r1 ** upper_n) / max(1.0e-12, 1.0 - r1)
                        use2 = r2 * (1.0 - r2 ** upper_n) / max(1.0e-12, 1.0 - r2)
                        upper_use = weight1 * use1 + (1.0 - weight1) * use2

                    upper_tail = weight1 * (r1 ** (upper_n + 1))
                    upper_tail = upper_tail + (1.0 - weight1) * (r2 ** (upper_n + 1))
                    upper_use = upper_use + upper_fraction * upper_tail

                    cohort_use = max(0.0, min(cohort, upper_use - lower_use))
                    layered[idx] = cohort - cohort_use
                    cumulative = upper

        shifted_aggregate = [0.0] * m
        shifted_layered = [0.0] * m

        for i in range(m - 1):
            shifted_aggregate[i] = aggregate[i + 1]
            shifted_layered[i] = layered[i + 1]

        if step < len(pipeline):
            arrival = max(0.0, pipeline[step])
            shifted_aggregate[m - 1] = arrival
            shifted_layered[m - 1] = arrival

        aggregate = shifted_aggregate
        layered = shifted_layered

    aggregate_effective = 0.0
    layered_effective = 0.0

    for i in range(m):
        relative_life = (i + 1.0) / m
        life_weight = relative_life ** A
        aggregate_effective = aggregate_effective + aggregate[i] * life_weight
        layered_effective = layered_effective + layered[i] * life_weight

    projected_effective = (1.0 - H) * aggregate_effective + H * layered_effective
    effective = (1.0 - B) * raw_effective + B * projected_effective
    gap = max(0.0, S - effective)
    order = min(C, G * gap)

    if order != order:
        return 0.0
    return max(0.0, order)
