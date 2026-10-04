def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    age_base = 0.30 # OPT_PARAM: {"type":"float","initial":0.30,"min":0.0,"max":1.5}
    age_slope = 0.20 # OPT_PARAM: {"type":"float","initial":0.20,"min":-0.2,"max":0.8}
    depletion_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":1.75}

    m = len(age)
    lead = int(L)
    x = [0.0 for _ in range(m)]
    for i in range(m):
        value = float(age[i])
        if value < 0.0:
            value = 0.0
        x[i] = value

    demand_variance_scale = (mu * cv) * (mu * cv)

    mf = f * mu
    vf = f * demand_variance_scale
    if mf > 0.0:
        af = vf / (mf * mf) - 1.0 / mf
        if af < 1.0:
            af = 1.0
        rootf = (af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2
        gf1 = rf1 / pf1
        gf2 = rf2 / pf2
    else:
        wf = 0.0
        rf1 = 0.0
        rf2 = 0.0
        gf1 = 0.0
        gf2 = 0.0

    ml = (1.0 - f) * mu
    vl = (1.0 - f) * demand_variance_scale
    if ml > 0.0:
        al = vl / (ml * ml) - 1.0 / ml
        if al < 1.0:
            al = 1.0
        rootl = (al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2
        gl1 = rl1 / pl1
        gl2 = rl2 / pl2
    else:
        wl = 0.0
        rl1 = 0.0
        rl2 = 0.0
        gl1 = 0.0
        gl2 = 0.0

    for h in range(lead):
        if mf > 0.0:
            cumulative = 0.0
            for i in range(m):
                stock = x[i]
                stop0 = wf * gf1 * (rf1 ** cumulative) + (1.0 - wf) * gf2 * (rf2 ** cumulative)
                threshold = cumulative + stock
                stop1 = wf * gf1 * (rf1 ** threshold) + (1.0 - wf) * gf2 * (rf2 ** threshold)
                used = depletion_scale * (stop0 - stop1)
                if used < 0.0:
                    used = 0.0
                if used > stock:
                    used = stock
                x[i] = stock - used
                cumulative = threshold

        if ml > 0.0:
            cumulative = 0.0
            for i in range(m - 1, -1, -1):
                stock = x[i]
                stop0 = wl * gl1 * (rl1 ** cumulative) + (1.0 - wl) * gl2 * (rl2 ** cumulative)
                threshold = cumulative + stock
                stop1 = wl * gl1 * (rl1 ** threshold) + (1.0 - wl) * gl2 * (rl2 ** threshold)
                used = depletion_scale * (stop0 - stop1)
                if used < 0.0:
                    used = 0.0
                if used > stock:
                    used = stock
                x[i] = stock - used
                cumulative = threshold

        for i in range(m - 1):
            x[i] = x[i + 1]
        if m > 0:
            x[m - 1] = 0.0

        if h < lead - 1 and h < len(pipeline) and m > 0:
            arrival = float(pipeline[h])
            if arrival < 0.0:
                arrival = 0.0
            x[m - 1] = arrival

    effective_stock = 0.0
    for i in range(m):
        weight = age_base + age_slope * float(i)
        if weight < 0.0:
            weight = 0.0
        if weight > 2.0:
            weight = 2.0
        effective_stock = effective_stock + weight * x[i]

    order = S - effective_stock
    if not (order == order):
        order = 0.0
    if order < 0.0:
        order = 0.0
    if order > 1000000.0:
        order = 1000000.0
    return float(order)
