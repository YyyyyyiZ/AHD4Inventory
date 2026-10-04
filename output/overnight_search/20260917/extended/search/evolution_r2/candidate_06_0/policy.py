def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 15.0 # OPT_PARAM: {"type":"float","initial":15.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    W_old = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":6.0}
    W_mid = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":4.0}
    T_quiet = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":2.5}
    D_clear = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":2.5}
    E_pressure = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":8.0}
    H_external = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":5.0}
    R_future = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":1.5}

    m = len(age)
    inv = [0.0 for i in range(m)]
    quiet = [0.0 for i in range(m)]
    for i in range(m):
        stock = float(age[i])
        if stock != stock or stock < 0.0:
            stock = 0.0
        if stock > 1000000.0:
            stock = 1000000.0
        inv[i] = stock
        quiet[i] = stock

    g_f = float(f)
    if g_f != g_f:
        g_f = 0.0
    if g_f < 0.0:
        g_f = 0.0
    if g_f > 1.0:
        g_f = 1.0
    g_l = 1.0 - g_f

    demand_mean = float(mu)
    demand_cv = float(cv)
    if demand_mean != demand_mean or demand_mean < 0.0:
        demand_mean = 0.0
    if demand_cv != demand_cv or demand_cv < 0.0:
        demand_cv = 0.0

    mean_f = g_f * demand_mean
    mean_l = g_l * demand_mean
    demand_sd = demand_mean * demand_cv

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
            if arrival != arrival or arrival < 0.0:
                arrival = 0.0
            if arrival > 1000000.0:
                arrival = 1000000.0
            inv[m - 1] = inv[m - 1] + arrival
            quiet[m - 1] = quiet[m - 1] + arrival

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
            quiet[i] = quiet[i + 1]
        inv[m - 1] = 0.0
        quiet[m - 1] = 0.0

    no_demand_probability = (p0f * p0l) ** L
    quiet_blend = T_quiet * no_demand_probability
    if quiet_blend < 0.0:
        quiet_blend = 0.0
    if quiet_blend > 1.0:
        quiet_blend = 1.0

    state = [0.0 for i in range(m)]
    effective = 0.0
    for i in range(m):
        stock = inv[i] + quiet_blend * (quiet[i] - inv[i])
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
            weight = W_mid + (1.0 - W_mid) * (2.0 * x - 1.0)
        effective = effective + weight * stock

    prefix = 0.0
    expiry_pressure = 0.0
    for i in range(m):
        prefix = prefix + state[i]
        clearance = D_clear * mean_f * (i + 1.0)
        excess = prefix - clearance
        if excess > expiry_pressure:
            expiry_pressure = excess

    base_gap = S - effective - E_pressure * g_l * expiry_pressure
    if base_gap != base_gap:
        base_gap = 0.0
    if base_gap < 0.0:
        base_gap = 0.0
    if base_gap > C:
        base_gap = C

    system0 = [0.0 for i in range(m)]
    system1 = [0.0 for i in range(m)]
    for i in range(m):
        system0[i] = state[i]
        system1[i] = state[i]
    system1[m - 1] = system1[m - 1] + base_gap

    waste0 = 0.0
    waste1 = 0.0
    future_arrival = R_future * demand_mean

    for h in range(m):
        if h > 0:
            system0[m - 1] = system0[m - 1] + future_arrival
            system1[m - 1] = system1[m - 1] + future_arrival

        for branch in range(2):
            if branch == 0:
                work = system0
            else:
                work = system1

            if mean_f > 0.0:
                cumulative = 0.0
                expected_previous = 0.0
                for i in range(m):
                    stock = work[i]
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
                    work[i] = stock - consumed
                    expected_previous = expected_cumulative

            if mean_l > 0.0:
                cumulative = 0.0
                expected_previous = 0.0
                for k in range(m):
                    i = m - 1 - k
                    stock = work[i]
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
                    work[i] = stock - consumed
                    expected_previous = expected_cumulative

            if branch == 0:
                waste0 = waste0 + work[0]
            else:
                waste1 = waste1 + work[0]

            for i in range(m - 1):
                work[i] = work[i + 1]
            work[m - 1] = 0.0

    externality = waste1 - waste0
    if externality < 0.0:
        externality = 0.0
    if externality > base_gap:
        externality = base_gap

    gap = base_gap - H_external * externality
    if gap != gap:
        gap = 0.0
    if gap < 0.0:
        gap = 0.0
    if gap > C:
        gap = C
    return float(gap)
