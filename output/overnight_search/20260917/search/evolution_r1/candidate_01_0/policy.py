def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":10.0}
    B = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":1.0}
    D = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.8}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}

    m = len(age)
    projected = [0.0] * m
    no_demand = [0.0] * m

    for i in range(m):
        projected[i] = max(0.0, age[i])
        no_demand[i] = max(0.0, age[i])

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
                cumulative = 0.0

                for pos in range(m):
                    if stream == 0:
                        idx = pos
                    else:
                        idx = m - 1 - pos

                    x = max(0.0, projected[idx])
                    lower = cumulative
                    upper = cumulative + x
                    values = [0.0, 0.0]

                    for side in range(2):
                        if side == 0:
                            t = lower
                        else:
                            t = upper

                        n = int(t)
                        fraction = t - n
                        e1 = 0.0
                        e2 = 0.0

                        if n > 0:
                            e1 = r1 * (1.0 - r1 ** n) / (1.0 - r1)
                            e2 = r2 * (1.0 - r2 ** n) / (1.0 - r2)

                        e1 = e1 + fraction * (r1 ** (n + 1))
                        e2 = e2 + fraction * (r2 ** (n + 1))
                        values[side] = weight1 * e1 + (1.0 - weight1) * e2

                    consumed = D * max(0.0, values[1] - values[0])
                    consumed = min(x, consumed)
                    projected[idx] = x - consumed
                    cumulative = upper

        shifted = [0.0] * m
        shifted_no_demand = [0.0] * m

        for i in range(m - 1):
            shifted[i] = projected[i + 1]
            shifted_no_demand[i] = no_demand[i + 1]

        if step < len(pipeline):
            arrival = max(0.0, pipeline[step])
            shifted[m - 1] = arrival
            shifted_no_demand[m - 1] = arrival

        projected = shifted
        no_demand = shifted_no_demand

    expected_effective = 0.0
    maximum_effective = 0.0

    for i in range(m):
        relative_life = (i + 1.0) / m
        weight = relative_life ** A
        expected_effective = expected_effective + projected[i] * weight
        maximum_effective = maximum_effective + no_demand[i] * weight

    effective = B * expected_effective + (1.0 - B) * maximum_effective
    order = S - K * effective
    order = max(0.0, min(C, order))

    if order != order:
        return 0.0
    return order
