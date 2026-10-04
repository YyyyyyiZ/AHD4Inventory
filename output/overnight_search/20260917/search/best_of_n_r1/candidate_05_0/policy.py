def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    CREDIT = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.6}
    AGE_DISCOUNT = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.5}
    TAIL_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.35,"max":2.5}
    RISK = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}

    m = len(age)
    x = [float(age[i]) for i in range(m)]
    xv = [0.0 for i in range(m)]

    mf = f * mu
    ml = (1.0 - f) * mu
    demand_sd = mu * cv

    if mf > 0.0:
        vf = f * demand_sd * demand_sd
        af = vf / (mf * mf) - 1.0 / mf
        df = af * af - 1.0
        if df < 0.0:
            df = 0.0
        sf = df ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        wf = 1.0 / bf
        rf1 = mf * bf / (2.0 + mf * bf)
        rf2 = mf * cf / (2.0 + mf * cf)
    else:
        wf = 0.0
        rf1 = 0.0
        rf2 = 0.0

    if ml > 0.0:
        vl = (1.0 - f) * demand_sd * demand_sd
        al = vl / (ml * ml) - 1.0 / ml
        dl = al * al - 1.0
        if dl < 0.0:
            dl = 0.0
        sl = dl ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        wl = 1.0 / bl
        rl1 = ml * bl / (2.0 + ml * bl)
        rl2 = ml * cl / (2.0 + ml * cl)
    else:
        wl = 0.0
        rl1 = 0.0
        rl2 = 0.0

    lead = int(L)
    if lead < 0:
        lead = 0
    if lead > 10:
        lead = 10

    for step in range(lead):
        total = 0.0
        for i in range(m):
            if x[i] > 0.0:
                total = total + x[i]

        y = [0.0 for i in range(m)]
        yv = [0.0 for i in range(m)]
        prefix = 0.0

        if total > 0.0:
            for i in range(m):
                xi = x[i]
                if xi > 0.0:
                    nseg = int(xi)
                    if xi - float(nseg) > 0.000000001:
                        nseg = nseg + 1
                    if nseg < 1:
                        nseg = 1
                    if nseg > 80:
                        nseg = 80
                    width = xi / float(nseg)
                    local_mean = 0.0
                    local_var = 0.0

                    for h in range(nseg):
                        position = prefix + (float(h) + 0.5) * width
                        ef = (position + 0.5) / TAIL_SCALE
                        el = (total - position + 0.5) / TAIL_SCALE

                        if mf > 0.0:
                            pf = 1.0 - wf * (rf1 ** ef) - (1.0 - wf) * (rf2 ** ef)
                        else:
                            pf = 1.0

                        if ml > 0.0:
                            pl = 1.0 - wl * (rl1 ** el) - (1.0 - wl) * (rl2 ** el)
                        else:
                            pl = 1.0

                        if pf < 0.0:
                            pf = 0.0
                        if pf > 1.0:
                            pf = 1.0
                        if pl < 0.0:
                            pl = 0.0
                        if pl > 1.0:
                            pl = 1.0

                        ps = pf * pl
                        local_mean = local_mean + width * ps
                        local_var = local_var + width * ps * (1.0 - ps)

                    average_survival = local_mean / xi
                    y[i] = local_mean
                    yv[i] = local_var + xv[i] * average_survival * average_survival
                    prefix = prefix + xi

        next_x = [0.0 for i in range(m)]
        next_v = [0.0 for i in range(m)]
        for i in range(m - 1):
            next_x[i] = y[i + 1]
            next_v[i] = yv[i + 1]

        arrival = 0.0
        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival < 0.0:
                arrival = 0.0
        if m > 0:
            next_x[m - 1] = arrival
            next_v[m - 1] = 0.0

        x = next_x
        xv = next_v

    credit = 0.0
    credit_variance = 0.0
    for i in range(m):
        freshness = float(i + 1) / float(m)
        weight = CREDIT * (1.0 - AGE_DISCOUNT * (1.0 - freshness))
        if weight < 0.0:
            weight = 0.0
        if weight > 2.5:
            weight = 2.5
        credit = credit + weight * x[i]
        credit_variance = credit_variance + weight * weight * xv[i]

    if credit_variance < 0.0:
        credit_variance = 0.0
    q = S - credit + RISK * (credit_variance ** 0.5)

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return q
