def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 9.0 # OPT_PARAM: {"type":"float","initial":9.0,"min":0.0,"max":40.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":40.0}
    K = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":4.0}
    D = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    W = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":3.0}
    O = 0.4 # OPT_PARAM: {"type":"float","initial":0.4,"min":0.0,"max":3.0}
    Y = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    A = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.1,"max":5.0}

    m = len(age)
    work = [0.0 for i in range(m)]
    for i in range(m):
        v = float(age[i])
        if v == v and v > 0.0:
            work[i] = v

    for step in range(L):
        for stream in range(2):
            if stream == 0:
                g = f
            else:
                g = 1.0 - f

            if g > 0.0:
                mean_stream = g * mu
                variance_stream = g * (mu * cv) * (mu * cv)
                shape = variance_stream / (mean_stream * mean_stream) - 1.0 / mean_stream
                discriminant = shape * shape - 1.0
                if discriminant < 0.0:
                    discriminant = 0.0
                root = discriminant ** 0.5
                b = 1.0 + shape + root
                c = 1.0 + shape - root
                weight1 = 1.0 / b
                p1 = 2.0 / (2.0 + mean_stream * b)
                p2 = 2.0 / (2.0 + mean_stream * c)
                r1 = 1.0 - p1
                r2 = 1.0 - p2

                cumulative = 0.0
                for k in range(m):
                    if stream == 0:
                        i = k
                    else:
                        i = m - 1 - k

                    quantity = work[i]
                    points = [cumulative, cumulative + quantity]
                    truncated = [0.0, 0.0]

                    for e in range(2):
                        z = points[e] / D
                        n = int(z)
                        fraction = z - n

                        part1 = r1 * (1.0 - r1 ** n) / p1
                        part1 = part1 + fraction * (r1 ** (n + 1))
                        part2 = r2 * (1.0 - r2 ** n) / p2
                        part2 = part2 + fraction * (r2 ** (n + 1))

                        truncated[e] = D * (
                            weight1 * part1 + (1.0 - weight1) * part2
                        )

                    consumed = truncated[1] - truncated[0]
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > quantity:
                        consumed = quantity
                    work[i] = quantity - consumed
                    cumulative = cumulative + quantity

        for i in range(m - 1):
            work[i] = work[i + 1]
        if m > 0:
            work[m - 1] = 0.0

        if step < len(pipeline) and m > 0:
            arrival = float(pipeline[step])
            if arrival == arrival and arrival > 0.0:
                work[m - 1] = arrival

    effective = 0.0
    if m > 0:
        for i in range(m):
            x = (i + 1.0) / m
            weight = W + O * ((1.0 - x) ** A) + Y * (x ** A)
            effective = effective + weight * work[i]

    q = K * (S - effective)
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return q
