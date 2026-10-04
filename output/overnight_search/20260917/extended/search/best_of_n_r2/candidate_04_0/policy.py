def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    stale_weight = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-2.0,"max":5.0}
    stale_power = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.1,"max":8.0}

    m = len(age)
    x = [0.0 for i in range(m)]
    for i in range(m):
        x[i] = max(0.0, float(age[i]))

    gf = max(0.0, min(1.0, float(f)))
    gl = 1.0 - gf

    pf1 = 1.0
    pf2 = 1.0
    rf1 = 0.0
    rf2 = 0.0
    wf1 = 0.0
    if gf > 0.0:
        Mf = gf * mu
        Vf = gf * (mu * cv) * (mu * cv)
        af = Vf / (Mf * Mf) - 1.0 / Mf
        af = max(1.0, af)
        rootf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf1 = 1.0 / bf
        pf1 = 2.0 / (2.0 + Mf * bf)
        pf2 = 2.0 / (2.0 + Mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    pl1 = 1.0
    pl2 = 1.0
    rl1 = 0.0
    rl2 = 0.0
    wl1 = 0.0
    if gl > 0.0:
        Ml = gl * mu
        Vl = gl * (mu * cv) * (mu * cv)
        al = Vl / (Ml * Ml) - 1.0 / Ml
        al = max(1.0, al)
        rootl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl1 = 1.0 / bl
        pl1 = 2.0 / (2.0 + Ml * bl)
        pl2 = 2.0 / (2.0 + Ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + max(0.0, float(pipeline[t - 1]))

        if gf > 0.0:
            prefix = 0.0
            for i in range(m):
                xi = x[i]
                sale1 = (rf1 ** (prefix + 1.0)) * (1.0 - rf1 ** xi) / pf1
                sale2 = (rf2 ** (prefix + 1.0)) * (1.0 - rf2 ** xi) / pf2
                sale = demand_scale * (wf1 * sale1 + (1.0 - wf1) * sale2)
                sale = max(0.0, min(xi, sale))
                x[i] = xi - sale
                prefix = prefix + xi

        if gl > 0.0:
            prefix = 0.0
            for k in range(m):
                i = m - 1 - k
                xi = x[i]
                sale1 = (rl1 ** (prefix + 1.0)) * (1.0 - rl1 ** xi) / pl1
                sale2 = (rl2 ** (prefix + 1.0)) * (1.0 - rl2 ** xi) / pl2
                sale = demand_scale * (wl1 * sale1 + (1.0 - wl1) * sale2)
                sale = max(0.0, min(xi, sale))
                x[i] = xi - sale
                prefix = prefix + xi

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0

    projected = 0.0
    stale = 0.0
    denom = max(1.0, float(m - 1))
    for i in range(m):
        projected = projected + x[i]
        stale_fraction = float(m - 1 - i) / denom
        stale = stale + x[i] * (stale_fraction ** stale_power)

    raw = S - projected - stale_weight * stale
    return max(0.0, min(C, raw))
