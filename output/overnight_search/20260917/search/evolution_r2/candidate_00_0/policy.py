def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    D = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":2.5}
    A = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":8.0}
    W0 = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    R = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":2.0}

    m = len(age)
    mf = f * mu
    ml = (1.0 - f) * mu

    rhof = 0.0
    condf = 0.0
    if mf > 0.0:
        vf = f * (mu * cv) * (mu * cv)
        af = vf / (mf * mf) - 1.0 / mf
        sf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        p0f = wf * pf1 + (1.0 - wf) * pf2
        rhof = max(0.0, min(1.0, 1.0 - p0f))
        if rhof > 0.0:
            condf = mf / rhof

    rhol = 0.0
    condl = 0.0
    if ml > 0.0:
        vl = (1.0 - f) * (mu * cv) * (mu * cv)
        al = vl / (ml * ml) - 1.0 / ml
        sl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        p0l = wl * pl1 + (1.0 - wl) * pl2
        rhol = max(0.0, min(1.0, 1.0 - p0l))
        if rhol > 0.0:
            condl = ml / rhol

    mean_effective = 0.0
    second_effective = 0.0
    scenarios = 1 << (2 * L)

    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = age[i]

        probability = 1.0

        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + pipeline[t - 1]

            fifo_active = (s >> (2 * t)) & 1
            lifo_active = (s >> (2 * t + 1)) & 1

            if fifo_active == 1:
                probability = probability * rhof
                fifo_demand = D * condf
            else:
                probability = probability * (1.0 - rhof)
                fifo_demand = 0.0

            if lifo_active == 1:
                probability = probability * rhol
                lifo_demand = D * condl
            else:
                probability = probability * (1.0 - rhol)
                lifo_demand = 0.0

            remaining = fifo_demand
            for i in range(m):
                take = min(x[i], remaining)
                x[i] = x[i] - take
                remaining = remaining - take

            remaining = lifo_demand
            for j in range(m):
                i = m - 1 - j
                take = min(x[i], remaining)
                x[i] = x[i] - take
                remaining = remaining - take

            for i in range(m - 1):
                x[i] = x[i + 1]
            x[m - 1] = 0.0

        effective = 0.0
        for i in range(m):
            relative_life = (i + 1.0) / m
            weight = W0 + (1.0 - W0) * (relative_life ** A)
            effective = effective + weight * x[i]

        mean_effective = mean_effective + probability * effective
        second_effective = second_effective + probability * effective * effective

    variance_effective = max(0.0, second_effective - mean_effective * mean_effective)
    deviation_effective = variance_effective ** 0.5
    raw_order = S - K * mean_effective - R * deviation_effective
    return max(0.0, min(C, raw_order))
