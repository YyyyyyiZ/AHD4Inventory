def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":8.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    B = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.0}

    m = len(age)
    raw_effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        raw_effective = raw_effective + age[i] * (x ** A)

    pipeline_stock = 0.0
    for j in range(len(pipeline)):
        pipeline_stock = pipeline_stock + pipeline[j]
    raw_effective = raw_effective + P * pipeline_stock

    projected = [0.0] * m
    for i in range(m):
        projected[i] = age[i]

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
                r1 = 1.0 - p1
                r2 = 1.0 - p2

                available = 0.0
                for i in range(m):
                    available = available + projected[i]

                if available > 0.0:
                    n = int(available)
                    fraction = available - n
                    expected_use = 0.0
                    if n > 0:
                        expected_use = weight1 * r1 * (1.0 - r1 ** n) / (1.0 - r1)
                        expected_use = expected_use + (1.0 - weight1) * r2 * (1.0 - r2 ** n) / (1.0 - r2)
                    tail = weight1 * (r1 ** (n + 1))
                    tail = tail + (1.0 - weight1) * (r2 ** (n + 1))
                    expected_use = expected_use + fraction * tail
                    expected_use = max(0.0, min(available, expected_use))

                    remaining = expected_use
                    if stream == 0:
                        for i in range(m):
                            take = min(projected[i], remaining)
                            projected[i] = projected[i] - take
                            remaining = remaining - take
                    else:
                        for i in range(m - 1, -1, -1):
                            take = min(projected[i], remaining)
                            projected[i] = projected[i] - take
                            remaining = remaining - take

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = projected[i + 1]
        if step < len(pipeline):
            shifted[m - 1] = pipeline[step]
        projected = shifted

    projected_effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        projected_effective = projected_effective + projected[i] * (x ** A)

    effective = (1.0 - B) * raw_effective + B * projected_effective
    return max(0.0, min(C, S - effective))
