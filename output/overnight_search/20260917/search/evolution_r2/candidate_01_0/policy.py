def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    D = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.8}
    A = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":8.0}
    W0 = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    R = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}

    m = len(age)
    mf = f * mu
    ml = (1.0 - f) * mu

    fprob = [1.0, 0.0, 0.0]
    fp = [1.0, 1.0, 1.0]
    if mf > 0.0:
        vf = f * (mu * cv) * (mu * cv)
        af = vf / (mf * mf) - 1.0 / mf
        sf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        fprob[0] = wf * pf1 + (1.0 - wf) * pf2
        fprob[1] = wf * (1.0 - pf1)
        fprob[2] = (1.0 - wf) * (1.0 - pf2)
        fp[1] = pf1
        fp[2] = pf2

    lprob = [1.0, 0.0, 0.0]
    lp = [1.0, 1.0, 1.0]
    if ml > 0.0:
        vl = (1.0 - f) * (mu * cv) * (mu * cv)
        al = vl / (ml * ml) - 1.0 / ml
        sl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        lprob[0] = wl * pl1 + (1.0 - wl) * pl2
        lprob[1] = wl * (1.0 - pl1)
        lprob[2] = (1.0 - wl) * (1.0 - pl2)
        lp[1] = pl1
        lp[2] = pl2

    mean_effective = 0.0
    second_effective = 0.0
    scenarios = 3 ** (2 * L)

    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = age[i]

        code = s
        probability = 1.0

        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + pipeline[t - 1]

            fifo_state = code % 3
            code = code // 3
            lifo_state = code % 3
            code = code // 3

            probability = probability * fprob[fifo_state] * lprob[lifo_state]

            if fifo_state > 0:
                stock = 0.0
                for i in range(m):
                    stock = stock + x[i]
                pnow = fp[fifo_state]
                fifo_demand = D * (1.0 - (1.0 - pnow) ** stock) / pnow
                remaining = fifo_demand
                for i in range(m):
                    take = min(x[i], remaining)
                    x[i] = x[i] - take
                    remaining = remaining - take

            if lifo_state > 0:
                stock = 0.0
                for i in range(m):
                    stock = stock + x[i]
                pnow = lp[lifo_state]
                lifo_demand = D * (1.0 - (1.0 - pnow) ** stock) / pnow
                remaining = lifo_demand
                for j in range(m):
                    i = m - 1 - j
                    take = min(x[i], remaining)
                    x[i] = x[i] - take
                    remaining = remaining - take

            for i in range(m - 1):
                x[i] = x[i + 1]
            x[m - 1] = 0.0

        if probability > 0.0:
            effective = 0.0
            for i in range(m):
                relative_life = (i + 1.0) / m
                weight = W0 + (1.0 - W0) * (relative_life ** A)
                effective = effective + weight * x[i]
            mean_effective = mean_effective + probability * effective
            second_effective = second_effective + probability * effective * effective

    variance_effective = max(
        0.0, second_effective - mean_effective * mean_effective
    )
    deviation_effective = variance_effective ** 0.5
    raw_order = S - K * mean_effective - R * deviation_effective
    return max(0.0, min(C, raw_order))
