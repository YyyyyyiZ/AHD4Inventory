def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":40.0}
    KF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    KL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    W = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.0,"max":1.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":5.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":2.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        x[i] = max(0.0, age[i])

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + max(0.0, pipeline[t - 1])

        total = 0.0
        for i in range(m):
            total = total + x[i]

        sold_f = 0.0
        if f > 0.0 and total > 0.0:
            M = f * mu
            V = f * (mu * cv) * (mu * cv)
            aa = V / (M * M) - 1.0 / M
            root = max(0.0, aa * aa - 1.0) ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            weight1 = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            q1 = 1.0 - p1
            q2 = 1.0 - p2
            n = int(total)
            r = total - n
            e1 = q1 * (1.0 - q1 ** n) / p1 + r * q1 ** (n + 1)
            e2 = q2 * (1.0 - q2 ** n) / p2 + r * q2 ** (n + 1)
            sold_f = min(total, KF * (weight1 * e1 + (1.0 - weight1) * e2))

        remaining = sold_f
        for i in range(m):
            take = min(x[i], remaining)
            x[i] = x[i] - take
            remaining = remaining - take

        total = 0.0
        for i in range(m):
            total = total + x[i]

        sold_l = 0.0
        g = 1.0 - f
        if g > 0.0 and total > 0.0:
            M = g * mu
            V = g * (mu * cv) * (mu * cv)
            aa = V / (M * M) - 1.0 / M
            root = max(0.0, aa * aa - 1.0) ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            weight1 = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            q1 = 1.0 - p1
            q2 = 1.0 - p2
            n = int(total)
            r = total - n
            e1 = q1 * (1.0 - q1 ** n) / p1 + r * q1 ** (n + 1)
            e2 = q2 * (1.0 - q2 ** n) / p2 + r * q2 ** (n + 1)
            sold_l = min(total, KL * (weight1 * e1 + (1.0 - weight1) * e2))

        remaining = sold_l
        for j in range(m):
            i = m - 1 - j
            take = min(x[i], remaining)
            x[i] = x[i] - take
            remaining = remaining - take

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0

    effective = 0.0
    for i in range(m):
        life_fraction = (i + 1.0) / m
        weight = W + (1.0 - W) * life_fraction ** A
        effective = effective + weight * x[i]

    order = G * (S - effective)
    order = max(0.0, min(C, order))
    if order != order:
        return 0.0
    return order
