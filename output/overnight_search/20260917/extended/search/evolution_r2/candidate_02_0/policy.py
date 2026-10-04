def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 13.0 # OPT_PARAM: {"type":"float","initial":13.0,"min":0.0,"max":60.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    W_old = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":6.0}
    W_mid = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":6.0}
    W_young = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    D_clear = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":2.0}
    E = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    B = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.3}

    m = len(age)
    inv = [0.0 for i in range(m)]
    for i in range(m):
        stock = float(age[i])
        if stock < 0.0:
            stock = 0.0
        inv[i] = stock

    g_f = float(f)
    if g_f < 0.0:
        g_f = 0.0
    if g_f > 1.0:
        g_f = 1.0
    g_l = 1.0 - g_f

    fifo_active = g_f > 0.0
    lifo_active = g_l > 0.0

    wf = 0.0
    rf1 = 0.0
    rf2 = 0.0
    mf1 = 0.0
    mf2 = 0.0
    if fifo_active:
        mean_f = g_f * mu
        var_f = g_f * (mu * cv) * (mu * cv)
        af = var_f / (mean_f * mean_f) - 1.0 / mean_f
        root_f = af * af - 1.0
        if root_f < 0.0:
            root_f = 0.0
        root_f = root_f ** 0.5
        bf = 1.0 + af + root_f
        cf = 1.0 + af - root_f
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mean_f * bf)
        pf2 = 2.0 / (2.0 + mean_f * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2
        mf1 = rf1 / pf1
        mf2 = rf2 / pf2

    wl = 0.0
    rl1 = 0.0
    rl2 = 0.0
    ml1 = 0.0
    ml2 = 0.0
    if lifo_active:
        mean_l = g_l * mu
        var_l = g_l * (mu * cv) * (mu * cv)
        al = var_l / (mean_l * mean_l) - 1.0 / mean_l
        root_l = al * al - 1.0
        if root_l < 0.0:
            root_l = 0.0
        root_l = root_l ** 0.5
        bl = 1.0 + al + root_l
        cl = 1.0 + al - root_l
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + mean_l * bl)
        pl2 = 2.0 / (2.0 + mean_l * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2
        ml1 = rl1 / pl1
        ml2 = rl2 / pl2

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            arrival = float(pipeline[t - 1])
            if arrival < 0.0:
                arrival = 0.0
            inv[m - 1] = inv[m - 1] + arrival

        if fifo_active:
            cumulative = 0.0
            expected_previous = 0.0
            fifo_scale = B ** t
            for i in range(m):
                stock = inv[i]
                cumulative = cumulative + stock
                expected_cumulative = (
                    wf * mf1 * (1.0 - rf1 ** cumulative)
                    + (1.0 - wf) * mf2 * (1.0 - rf2 ** cumulative)
                )
                consumed = fifo_scale * (expected_cumulative - expected_previous)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > stock:
                    consumed = stock
                inv[i] = stock - consumed
                expected_previous = expected_cumulative

        if lifo_active:
            cumulative = 0.0
            expected_previous = 0.0
            correction_depth = t
            if fifo_active:
                correction_depth = correction_depth + 1
            lifo_scale = B ** correction_depth
            for k in range(m):
                i = m - 1 - k
                stock = inv[i]
                cumulative = cumulative + stock
                expected_cumulative = (
                    wl * ml1 * (1.0 - rl1 ** cumulative)
                    + (1.0 - wl) * ml2 * (1.0 - rl2 ** cumulative)
                )
                consumed = lifo_scale * (expected_cumulative - expected_previous)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > stock:
                    consumed = stock
                inv[i] = stock - consumed
                expected_previous = expected_cumulative

        for i in range(m - 1):
            inv[i] = inv[i + 1]
        inv[m - 1] = 0.0

    effective = 0.0
    for i in range(m):
        if m > 1:
            x = i / (m - 1.0)
        else:
            x = 1.0
        if x <= 0.5:
            weight = W_old + (W_mid - W_old) * (2.0 * x)
        else:
            weight = W_mid + (W_young - W_mid) * (2.0 * x - 1.0)
        effective = effective + weight * inv[i]

    prefix = 0.0
    expiry_pressure = 0.0
    for i in range(m):
        prefix = prefix + inv[i]
        clearance = D_clear * g_f * mu * (i + 1.0)
        excess = prefix - clearance
        if excess > expiry_pressure:
            expiry_pressure = excess

    gap = S - effective - E * g_l * expiry_pressure
    if gap != gap:
        gap = 0.0
    if gap < 0.0:
        gap = 0.0
    if gap > C:
        gap = C
    return float(gap)
