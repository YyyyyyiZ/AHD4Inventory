def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":2.5}
    AGE_POWER = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    DRAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}

    m = len(age)
    x = [0.0 for i in range(m)]
    for i in range(m):
        x[i] = max(0.0, float(age[i]))

    mf = f * mu
    ml = (1.0 - f) * mu
    base_var = (mu * cv) * (mu * cv)

    wf = 0.0
    rf1 = 0.0
    rf2 = 0.0
    if mf > 0.0:
        vf = f * base_var
        af = vf / (mf * mf) - 1.0 / mf
        zf = af * af - 1.0
        if zf < 0.0:
            zf = 0.0
        sf = zf ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    wl = 0.0
    rl1 = 0.0
    rl2 = 0.0
    if ml > 0.0:
        vl = (1.0 - f) * base_var
        al = vl / (ml * ml) - 1.0 / ml
        zl = al * al - 1.0
        if zl < 0.0:
            zl = 0.0
        sl = zl ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    lead = int(L)
    for t in range(lead):
        total = 0.0
        for i in range(m):
            total = total + x[i]

        fifo_served = 0.0
        if mf > 0.0 and total > 0.0:
            n = int(total)
            frac = total - float(n)
            e1 = 0.0
            e2 = 0.0
            if n > 0:
                e1 = rf1 * (1.0 - rf1 ** n) / (1.0 - rf1)
                e2 = rf2 * (1.0 - rf2 ** n) / (1.0 - rf2)
            e1 = e1 + frac * (rf1 ** (n + 1))
            e2 = e2 + frac * (rf2 ** (n + 1))
            fifo_served = DRAIN * (wf * e1 + (1.0 - wf) * e2)
            if fifo_served > total:
                fifo_served = total

        rem = fifo_served
        for i in range(m):
            take = x[i]
            if take > rem:
                take = rem
            x[i] = x[i] - take
            rem = rem - take

        total = 0.0
        for i in range(m):
            total = total + x[i]

        lifo_served = 0.0
        if ml > 0.0 and total > 0.0:
            n = int(total)
            frac = total - float(n)
            e1 = 0.0
            e2 = 0.0
            if n > 0:
                e1 = rl1 * (1.0 - rl1 ** n) / (1.0 - rl1)
                e2 = rl2 * (1.0 - rl2 ** n) / (1.0 - rl2)
            e1 = e1 + frac * (rl1 ** (n + 1))
            e2 = e2 + frac * (rl2 ** (n + 1))
            lifo_served = DRAIN * (wl * e1 + (1.0 - wl) * e2)
            if lifo_served > total:
                lifo_served = total

        rem = lifo_served
        for i in range(m - 1, -1, -1):
            take = x[i]
            if take > rem:
                take = rem
            x[i] = x[i] - take
            rem = rem - take

        for i in range(m - 1):
            x[i] = x[i + 1]
        if m > 0:
            x[m - 1] = 0.0

        if t < lead - 1 and t < len(pipeline) and m > 0:
            x[m - 1] = x[m - 1] + max(0.0, float(pipeline[t]))

    effective = 0.0
    exponent = AGE_POWER * 2.0 * f
    for i in range(m):
        relative_life = (i + 1.0) / float(m)
        weight = relative_life ** exponent
        effective = effective + weight * x[i]

    gap = S - effective
    order = GAIN * gap
    if order < 0.0 or order != order:
        order = 0.0
    if order > C:
        order = C
    return order
