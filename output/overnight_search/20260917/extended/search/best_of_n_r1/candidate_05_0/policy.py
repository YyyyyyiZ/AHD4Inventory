def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    Q = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    W0 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":2.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":5.0}

    m = len(age)
    if m == 0:
        return 0.0

    state = [float(age[i]) for i in range(m)]

    mf = f * mu
    ml = (1.0 - f) * mu
    base_variance = (mu * cv) * (mu * cv)
    vf = f * base_variance
    vl = (1.0 - f) * base_variance

    if mf > 0.0:
        af = vf / (mf * mf) - 1.0 / mf
        df = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + df
        cf = 1.0 + af - df
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2
    else:
        wf = 0.0
        pf1 = 1.0
        pf2 = 1.0
        rf1 = 0.0
        rf2 = 0.0

    if ml > 0.0:
        al = vl / (ml * ml) - 1.0 / ml
        dl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + dl
        cl = 1.0 + al - dl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2
    else:
        wl = 0.0
        pl1 = 1.0
        pl2 = 1.0
        rl1 = 0.0
        rl2 = 0.0

    for t in range(L):
        total = 0.0
        for i in range(m):
            total = total + state[i]

        fifo_sales = 0.0
        if mf > 0.0 and total > 0.0:
            n = int(total)
            fraction = total - n
            e1 = rf1 * (1.0 - rf1 ** n) / pf1 + fraction * rf1 ** (n + 1)
            e2 = rf2 * (1.0 - rf2 ** n) / pf2 + fraction * rf2 ** (n + 1)
            fifo_sales = K * (wf * e1 + (1.0 - wf) * e2)
            fifo_sales = min(total, max(0.0, fifo_sales))

        remaining = fifo_sales
        for i in range(m):
            take = min(state[i], remaining)
            state[i] = state[i] - take
            remaining = remaining - take

        total = 0.0
        for i in range(m):
            total = total + state[i]

        lifo_sales = 0.0
        if ml > 0.0 and total > 0.0:
            n = int(total)
            fraction = total - n
            e1 = rl1 * (1.0 - rl1 ** n) / pl1 + fraction * rl1 ** (n + 1)
            e2 = rl2 * (1.0 - rl2 ** n) / pl2 + fraction * rl2 ** (n + 1)
            lifo_sales = K * (wl * e1 + (1.0 - wl) * e2)
            lifo_sales = min(total, max(0.0, lifo_sales))

        remaining = lifo_sales
        for j in range(m):
            i = m - 1 - j
            take = min(state[i], remaining)
            state[i] = state[i] - take
            remaining = remaining - take

        for i in range(m - 1):
            state[i] = state[i + 1]
        state[m - 1] = 0.0

        if t < L - 1 and t < len(pipeline):
            state[m - 1] = state[m - 1] + float(pipeline[t])

    effective = 0.0
    for i in range(m):
        relative_life = (i + 1.0) / m
        weight = W0 + (1.0 - W0) * relative_life ** P
        effective = effective + weight * state[i]

    order = S - effective
    return max(0.0, min(Q, order))
