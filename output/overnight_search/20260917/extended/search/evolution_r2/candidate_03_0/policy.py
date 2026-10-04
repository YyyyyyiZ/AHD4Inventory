def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    W_old = 2.2 # OPT_PARAM: {"type":"float","initial":2.2,"min":0.0,"max":6.0}
    W_early = 1.1 # OPT_PARAM: {"type":"float","initial":1.1,"min":0.0,"max":6.0}
    W_late = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":6.0}
    D_fifo = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}
    D_lifo = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":3.0}
    Y_block = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    Z_clear = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.5}
    E_max = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    E_avg = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":6.0}

    m = len(age)
    inv = [0.0 for i in range(m)]
    for i in range(m):
        stock = float(age[i])
        if stock != stock or stock < 0.0:
            stock = 0.0
        if stock > 1000000.0:
            stock = 1000000.0
        inv[i] = stock

    g_f = float(f)
    if g_f != g_f:
        g_f = 0.0
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
            if arrival != arrival or arrival < 0.0:
                arrival = 0.0
            if arrival > 1000000.0:
                arrival = 1000000.0
            inv[m - 1] = inv[m - 1] + arrival

        if fifo_active:
            cumulative = 0.0
            expected_previous = 0.0
            for i in range(m):
                stock = inv[i]
                cumulative = cumulative + stock
                expected_cumulative = (
                    wf * mf1 * (1.0 - rf1 ** cumulative)
                    + (1.0 - wf) * mf2 * (1.0 - rf2 ** cumulative)
                )
                consumed = expected_cumulative - expected_previous
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > stock:
                    consumed = stock
                inv[i] = stock - consumed
                expected_previous = expected_cumulative

        if lifo_active:
            cumulative = 0.0
            expected_previous = 0.0
            for k in range(m):
                i = m - 1 - k
                stock = inv[i]
                cumulative = cumulative + stock
                expected_cumulative = (
                    wl * ml1 * (1.0 - rl1 ** cumulative)
                    + (1.0 - wl) * ml2 * (1.0 - rl2 ** cumulative)
                )
                consumed = expected_cumulative - expected_previous
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
    total_projected = 0.0
    for i in range(m):
        total_projected = total_projected + inv[i]
        if m > 1:
            x = i / (m - 1.0)
        else:
            x = 1.0
        if x <= 1.0 / 3.0:
            u = 3.0 * x
            weight = W_old + (W_early - W_old) * u
        elif x <= 2.0 / 3.0:
            u = 3.0 * x - 1.0
            weight = W_early + (W_late - W_early) * u
        else:
            u = 3.0 * x - 2.0
            weight = W_late + (1.0 - W_late) * u
        effective = effective + weight * inv[i]

    prefix = 0.0
    pressure_max = 0.0
    pressure_sum = 0.0
    for i in range(m):
        prefix = prefix + inv[i]
        younger = total_projected - prefix
        if younger < 0.0:
            younger = 0.0

        horizon = i + 1.0

        fifo_budget = g_f * mu * horizon
        fifo_safety = Z_clear * mu * cv * (g_f * horizon) ** 0.5
        fifo_budget = fifo_budget - fifo_safety
        if fifo_budget < 0.0:
            fifo_budget = 0.0
        fifo_budget = D_fifo * fifo_budget

        lifo_budget = g_l * mu * horizon
        lifo_safety = Z_clear * mu * cv * (g_l * horizon) ** 0.5
        lifo_budget = lifo_budget - lifo_safety
        if lifo_budget < 0.0:
            lifo_budget = 0.0
        lifo_budget = D_lifo * lifo_budget - Y_block * younger
        if lifo_budget < 0.0:
            lifo_budget = 0.0

        excess = prefix - fifo_budget - lifo_budget
        if excess > 0.0:
            urgency = (m - i) / float(m)
            pressure = urgency * excess
            pressure_sum = pressure_sum + pressure
            if pressure > pressure_max:
                pressure_max = pressure

    pressure_avg = pressure_sum / float(m)
    gap = S - effective - E_max * pressure_max - E_avg * pressure_avg

    if gap != gap:
        gap = 0.0
    if gap < 0.0:
        gap = 0.0
    if gap > C:
        gap = C
    if gap > 1000000.0:
        gap = 1000000.0
    return float(gap)
