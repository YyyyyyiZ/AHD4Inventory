def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 13.0 # OPT_PARAM: {"type":"float","initial":13.0,"min":0.0,"max":60.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    W_old = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":6.0}
    W_mid = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":6.0}
    W_young = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    T_low = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":2.5}
    D_fifo = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":2.5}
    D_lifo = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":2.5}
    U_doomed = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":3.0}
    H_external = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":5.0}
    A_shield = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}

    m = len(age)
    inv = [0.0 for i in range(m)]
    low = [0.0 for i in range(m)]
    for i in range(m):
        stock = float(age[i])
        if stock < 0.0:
            stock = 0.0
        inv[i] = stock
        low[i] = stock

    g_f = float(f)
    if g_f < 0.0:
        g_f = 0.0
    if g_f > 1.0:
        g_f = 1.0
    g_l = 1.0 - g_f

    mean_f = g_f * float(mu)
    mean_l = g_l * float(mu)
    demand_sd = float(mu) * float(cv)

    wf = 0.0
    rf1 = 0.0
    rf2 = 0.0
    mf1 = 0.0
    mf2 = 0.0
    p0f = 1.0
    if mean_f > 0.0:
        var_f = g_f * demand_sd * demand_sd
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
        p0f = wf * pf1 + (1.0 - wf) * pf2

    wl = 0.0
    rl1 = 0.0
    rl2 = 0.0
    ml1 = 0.0
    ml2 = 0.0
    p0l = 1.0
    if mean_l > 0.0:
        var_l = g_l * demand_sd * demand_sd
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
        p0l = wl * pl1 + (1.0 - wl) * pl2

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            arrival = float(pipeline[t - 1])
            if arrival < 0.0:
                arrival = 0.0
            inv[m - 1] = inv[m - 1] + arrival
            low[m - 1] = low[m - 1] + arrival

        if mean_f > 0.0:
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

        if mean_l > 0.0:
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
            low[i] = low[i + 1]
        inv[m - 1] = 0.0
        low[m - 1] = 0.0

    no_demand_probability = (p0f * p0l) ** L
    blend = T_low * no_demand_probability
    if blend < 0.0:
        blend = 0.0
    if blend > 1.0:
        blend = 1.0

    state = [0.0 for i in range(m)]
    effective = 0.0
    for i in range(m):
        stock = inv[i] + blend * (low[i] - inv[i])
        if stock < 0.0:
            stock = 0.0
        state[i] = stock
        if m > 1:
            x = i / (m - 1.0)
        else:
            x = 1.0
        if x <= 0.5:
            weight = W_old + (W_mid - W_old) * (2.0 * x)
        else:
            weight = W_mid + (W_young - W_mid) * (2.0 * x - 1.0)
        effective = effective + weight * stock

    pressure0 = 0.0
    prefix = 0.0
    for i in range(m):
        prefix = prefix + state[i]
        younger = 0.0
        for j in range(i + 1, m):
            younger = younger + state[j]

        remaining_young = younger
        consumed_young = 0.0
        horizon = i + 1
        if mean_l > 0.0:
            for h in range(horizon):
                consumed = (
                    wl * ml1 * (1.0 - rl1 ** remaining_young)
                    + (1.0 - wl) * ml2 * (1.0 - rl2 ** remaining_young)
                )
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > remaining_young:
                    consumed = remaining_young
                remaining_young = remaining_young - consumed
                consumed_young = consumed_young + consumed

        lifo_reach = horizon * mean_l - consumed_young
        if lifo_reach < 0.0:
            lifo_reach = 0.0
        clearance = D_fifo * horizon * mean_f + D_lifo * lifo_reach
        excess = prefix - clearance
        if excess > pressure0:
            pressure0 = excess

    base_gap = S - effective + U_doomed * pressure0
    if base_gap < 0.0:
        base_gap = 0.0
    if base_gap > C:
        base_gap = C

    pressure_order = 0.0
    prefix = 0.0
    for i in range(m):
        prefix = prefix + state[i]
        younger = A_shield * base_gap
        for j in range(i + 1, m):
            younger = younger + state[j]

        remaining_young = younger
        consumed_young = 0.0
        horizon = i + 1
        if mean_l > 0.0:
            for h in range(horizon):
                consumed = (
                    wl * ml1 * (1.0 - rl1 ** remaining_young)
                    + (1.0 - wl) * ml2 * (1.0 - rl2 ** remaining_young)
                )
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > remaining_young:
                    consumed = remaining_young
                remaining_young = remaining_young - consumed
                consumed_young = consumed_young + consumed

        lifo_reach = horizon * mean_l - consumed_young
        if lifo_reach < 0.0:
            lifo_reach = 0.0
        clearance = D_fifo * horizon * mean_f + D_lifo * lifo_reach
        excess = prefix - clearance
        if excess > pressure_order:
            pressure_order = excess

    externality = pressure_order - pressure0
    if externality < 0.0:
        externality = 0.0

    gap = base_gap - H_external * g_l * externality
    if gap != gap:
        gap = 0.0
    if gap < 0.0:
        gap = 0.0
    if gap > C:
        gap = C
    return float(gap)
