def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    alpha = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":4.0}
    old_boost = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":4.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.5,"max":1.8}
    gain = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":1.8}

    m = len(age)
    state = [max(0.0, float(age[i])) for i in range(m)]

    mean_fifo = f * mu
    var_fifo = f * (mu * cv) * (mu * cv)
    mean_lifo = (1.0 - f) * mu
    var_lifo = (1.0 - f) * (mu * cv) * (mu * cv)

    if mean_fifo > 0.0:
        af = var_fifo / (mean_fifo * mean_fifo) - 1.0 / mean_fifo
        rootf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mean_fifo * bf)
        pf2 = 2.0 / (2.0 + mean_fifo * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2
    else:
        wf = 0.0
        pf1 = 1.0
        pf2 = 1.0
        rf1 = 0.0
        rf2 = 0.0

    if mean_lifo > 0.0:
        al = var_lifo / (mean_lifo * mean_lifo) - 1.0 / mean_lifo
        rootl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + mean_lifo * bl)
        pl2 = 2.0 / (2.0 + mean_lifo * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2
    else:
        wl = 0.0
        pl1 = 1.0
        pl2 = 1.0
        rl1 = 0.0
        rl2 = 0.0

    for step in range(L):
        if mean_fifo > 0.0:
            cumulative = 0.0
            excess_before = demand_scale * mean_fifo
            for i in range(m):
                units = state[i]
                cumulative_after = cumulative + units
                excess_after = demand_scale * (
                    wf * (rf1 ** (cumulative_after / demand_scale + 1.0)) / pf1
                    + (1.0 - wf) * (rf2 ** (cumulative_after / demand_scale + 1.0)) / pf2
                )
                consumed = min(units, max(0.0, excess_before - excess_after))
                state[i] = units - consumed
                cumulative = cumulative_after
                excess_before = excess_after

        if mean_lifo > 0.0:
            cumulative = 0.0
            excess_before = demand_scale * mean_lifo
            for k in range(m):
                i = m - 1 - k
                units = state[i]
                cumulative_after = cumulative + units
                excess_after = demand_scale * (
                    wl * (rl1 ** (cumulative_after / demand_scale + 1.0)) / pl1
                    + (1.0 - wl) * (rl2 ** (cumulative_after / demand_scale + 1.0)) / pl2
                )
                consumed = min(units, max(0.0, excess_before - excess_after))
                state[i] = units - consumed
                cumulative = cumulative_after
                excess_before = excess_after

        for i in range(m - 1):
            state[i] = state[i + 1]
        state[m - 1] = 0.0

        if step < len(pipeline):
            state[m - 1] = state[m - 1] + max(0.0, float(pipeline[step]))

    effective = 0.0
    for i in range(m):
        life_fraction = (i + 1.0) / m
        weight = life_fraction ** alpha + old_boost * (1.0 - life_fraction)
        effective = effective + weight * state[i]

    raw_order = mu + gain * (S - mu - effective)
    return max(0.0, min(C, raw_order))
