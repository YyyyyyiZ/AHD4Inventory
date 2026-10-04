def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 13.0 # OPT_PARAM: {"type":"float","initial":13.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    W_old = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":6.0}
    W_mid = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":6.0}
    B_inv = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}
    B_exp = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}
    D_fifo = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":2.5}
    D_lifo = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":2.5}
    Y_shield = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    E_exp = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.0,"max":8.0}

    m = len(age)
    lead = int(L)
    if lead < 0:
        lead = 0

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
        if p0f < 0.0:
            p0f = 0.0
        if p0f > 1.0:
            p0f = 1.0

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
        if p0l < 0.0:
            p0l = 0.0
        if p0l > 1.0:
            p0l = 1.0

    positive_f = 1.0 - p0f
    positive_l = 1.0 - p0l
    scenario_count = 4 ** lead

    probability_sum = 0.0
    mean_effective = 0.0
    mean_pressure = 0.0
    zero_effective = 0.0
    zero_pressure = 0.0
    zero_probability = 0.0

    for scenario in range(scenario_count):
        inv = [0.0 for i in range(m)]
        for i in range(m):
            stock = float(age[i])
            if stock != stock or stock < 0.0:
                stock = 0.0
            if stock > 1000000.0:
                stock = 1000000.0
            inv[i] = stock

        code = scenario
        probability = 1.0

        for t in range(lead):
            fifo_positive = code % 2
            code = code // 2
            lifo_positive = code % 2
            code = code // 2

            if fifo_positive == 0:
                probability = probability * p0f
            else:
                probability = probability * positive_f

            if lifo_positive == 0:
                probability = probability * p0l
            else:
                probability = probability * positive_l

            if t > 0 and t - 1 < len(pipeline) and m > 0:
                arrival = float(pipeline[t - 1])
                if arrival != arrival or arrival < 0.0:
                    arrival = 0.0
                if arrival > 1000000.0:
                    arrival = 1000000.0
                inv[m - 1] = inv[m - 1] + arrival

            if fifo_positive == 1 and positive_f > 0.0:
                cumulative = 0.0
                previous = 0.0
                for i in range(m):
                    stock = inv[i]
                    cumulative = cumulative + stock
                    unconditional = (
                        wf * mf1 * (1.0 - rf1 ** cumulative)
                        + (1.0 - wf) * mf2 * (1.0 - rf2 ** cumulative)
                    )
                    conditional = unconditional / positive_f
                    consumed = conditional - previous
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > stock:
                        consumed = stock
                    inv[i] = stock - consumed
                    previous = conditional

            if lifo_positive == 1 and positive_l > 0.0:
                cumulative = 0.0
                previous = 0.0
                for k in range(m):
                    i = m - 1 - k
                    stock = inv[i]
                    cumulative = cumulative + stock
                    unconditional = (
                        wl * ml1 * (1.0 - rl1 ** cumulative)
                        + (1.0 - wl) * ml2 * (1.0 - rl2 ** cumulative)
                    )
                    conditional = unconditional / positive_l
                    consumed = conditional - previous
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > stock:
                        consumed = stock
                    inv[i] = stock - consumed
                    previous = conditional

            for i in range(m - 1):
                inv[i] = inv[i + 1]
            if m > 0:
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
                weight = W_mid + (1.0 - W_mid) * (2.0 * x - 1.0)
            effective = effective + weight * inv[i]

        pressure = 0.0
        prefix = 0.0
        for i in range(m):
            prefix = prefix + inv[i]
            younger = 0.0
            for j in range(i + 1, m):
                younger = younger + inv[j]
            horizon = i + 1.0
            lifo_reach = horizon * mean_l - Y_shield * younger
            if lifo_reach < 0.0:
                lifo_reach = 0.0
            clearance = (
                D_fifo * horizon * mean_f
                + D_lifo * lifo_reach
            )
            excess = prefix - clearance
            if excess > pressure:
                pressure = excess

        probability_sum = probability_sum + probability
        mean_effective = mean_effective + probability * effective
        mean_pressure = mean_pressure + probability * pressure

        if scenario == 0:
            zero_effective = effective
            zero_pressure = pressure
            zero_probability = probability

    if probability_sum > 0.0:
        mean_effective = mean_effective / probability_sum
        mean_pressure = mean_pressure / probability_sum
        zero_probability = zero_probability / probability_sum

    inv_blend = B_inv * zero_probability
    exp_blend = B_exp * zero_probability
    if inv_blend < 0.0:
        inv_blend = 0.0
    if inv_blend > 1.0:
        inv_blend = 1.0
    if exp_blend < 0.0:
        exp_blend = 0.0
    if exp_blend > 1.0:
        exp_blend = 1.0

    effective_inventory = mean_effective
    if zero_effective > mean_effective:
        effective_inventory = (
            mean_effective
            + inv_blend * (zero_effective - mean_effective)
        )

    expiry_pressure = mean_pressure
    if zero_pressure > mean_pressure:
        expiry_pressure = (
            mean_pressure
            + exp_blend * (zero_pressure - mean_pressure)
        )

    gap = S - effective_inventory - E_exp * g_l * expiry_pressure
    if gap != gap:
        gap = 0.0
    if gap < 0.0:
        gap = 0.0
    if gap > C:
        gap = C
    return float(gap)
