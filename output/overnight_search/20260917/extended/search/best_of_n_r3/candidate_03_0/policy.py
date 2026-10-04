def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":3.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":4.0}
    OLD = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    SALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.3,"max":1.8}

    m = len(age)
    stock = [0.0] * m
    for i in range(m):
        stock[i] = max(0.0, float(age[i]))

    for t in range(L):
        for group in range(2):
            if group == 0:
                g = f
            else:
                g = 1.0 - f

            total = 0.0
            for i in range(m):
                total = total + stock[i]

            sale = 0.0
            if g > 0.0 and total > 0.0:
                M = g * mu
                V = g * (mu * cv) * (mu * cv)
                shape = V / (M * M) - 1.0 / M
                root = max(0.0, shape * shape - 1.0) ** 0.5
                b = 1.0 + shape + root
                c = 1.0 + shape - root
                p1 = 2.0 / (2.0 + M * b)
                p2 = 2.0 / (2.0 + M * c)
                r1 = 1.0 - p1
                r2 = 1.0 - p2
                n = int(total)
                frac = total - n
                e1 = r1 * (1.0 - r1 ** n) / p1 + frac * r1 ** (n + 1)
                e2 = r2 * (1.0 - r2 ** n) / p2 + frac * r2 ** (n + 1)
                expected = e1 / b + e2 / c
                sale = min(total, SALE * expected)

            remaining = sale
            if group == 0:
                for i in range(m):
                    used = min(stock[i], remaining)
                    stock[i] = stock[i] - used
                    remaining = remaining - used
            else:
                for k in range(m):
                    i = m - 1 - k
                    used = min(stock[i], remaining)
                    stock[i] = stock[i] - used
                    remaining = remaining - used

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = stock[i + 1]
        if t < len(pipeline):
            shifted[m - 1] = max(0.0, float(pipeline[t]))
        else:
            shifted[m - 1] = 0.0
        stock = shifted

    effective = 0.0
    routing_factor = (1.0 - f) ** 3
    for i in range(m):
        x = (i + 1.0) / m
        weight = x ** A + OLD * routing_factor * (1.0 - x)
        effective = effective + weight * stock[i]

    q = S - G * effective
    q = max(0.0, min(C, q))
    if q != q:
        q = 0.0
    return float(q)
