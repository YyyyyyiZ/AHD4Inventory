def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    lead_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":1.75}
    future_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":1.75}
    fifo_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    lifo_credit = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":2.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        v = float(age[i])
        if v < 0.0 or v != v:
            v = 0.0
        x[i] = v

    MF = f * mu
    ML = (1.0 - f) * mu
    base_variance = (mu * cv) * (mu * cv)

    fw = 0.0
    fr1 = 0.0
    fr2 = 0.0
    fm1 = 0.0
    fm2 = 0.0
    if MF > 0.0:
        VF = f * base_variance
        fa = VF / (MF * MF) - 1.0 / MF
        fdisc = fa * fa - 1.0
        if fdisc < 0.0:
            fdisc = 0.0
        froot = fdisc ** 0.5
        fb = 1.0 + fa + froot
        fc = 1.0 + fa - froot
        fw = 1.0 / fb
        fp1 = 2.0 / (2.0 + MF * fb)
        fp2 = 2.0 / (2.0 + MF * fc)
        fr1 = 1.0 - fp1
        fr2 = 1.0 - fp2
        fm1 = fr1 / fp1
        fm2 = fr2 / fp2

    lw = 0.0
    lr1 = 0.0
    lr2 = 0.0
    lm1 = 0.0
    lm2 = 0.0
    if ML > 0.0:
        VL = (1.0 - f) * base_variance
        la = VL / (ML * ML) - 1.0 / ML
        ldisc = la * la - 1.0
        if ldisc < 0.0:
            ldisc = 0.0
        lroot = ldisc ** 0.5
        lb = 1.0 + la + lroot
        lc = 1.0 + la - lroot
        lw = 1.0 / lb
        lp1 = 2.0 / (2.0 + ML * lb)
        lp2 = 2.0 / (2.0 + ML * lc)
        lr1 = 1.0 - lp1
        lr2 = 1.0 - lp2
        lm1 = lr1 / lp1
        lm2 = lr2 / lp2

    for step in range(L):
        if MF > 0.0:
            cumulative = 0.0
            previous_served = 0.0
            for i in range(m):
                stock = x[i]
                cumulative = cumulative + stock
                served = fw * fm1 * (1.0 - fr1 ** cumulative)
                served = served + (1.0 - fw) * fm2 * (1.0 - fr2 ** cumulative)
                use = lead_scale * (served - previous_served)
                if use < 0.0:
                    use = 0.0
                if use > stock:
                    use = stock
                x[i] = stock - use
                previous_served = served

        if ML > 0.0:
            cumulative = 0.0
            previous_served = 0.0
            for k in range(m):
                i = m - 1 - k
                stock = x[i]
                cumulative = cumulative + stock
                served = lw * lm1 * (1.0 - lr1 ** cumulative)
                served = served + (1.0 - lw) * lm2 * (1.0 - lr2 ** cumulative)
                use = lead_scale * (served - previous_served)
                if use < 0.0:
                    use = 0.0
                if use > stock:
                    use = stock
                x[i] = stock - use
                previous_served = served

        for i in range(m - 1):
            x[i] = x[i + 1]

        arrival = 0.0
        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival < 0.0 or arrival != arrival:
                arrival = 0.0
        x[m - 1] = arrival

    yf = [0.0] * m
    yb = [0.0] * m
    for i in range(m):
        yf[i] = x[i]
        yb[i] = x[i]

    fifo_utility = 0.0
    for step in range(m):
        if MF > 0.0:
            cumulative = 0.0
            previous_served = 0.0
            for i in range(m):
                stock = yf[i]
                cumulative = cumulative + stock
                served = fw * fm1 * (1.0 - fr1 ** cumulative)
                served = served + (1.0 - fw) * fm2 * (1.0 - fr2 ** cumulative)
                use = future_scale * (served - previous_served)
                if use < 0.0:
                    use = 0.0
                if use > stock:
                    use = stock
                yf[i] = stock - use
                fifo_utility = fifo_utility + use
                previous_served = served

        for i in range(m - 1):
            yf[i] = yf[i + 1]
        yf[m - 1] = 0.0

    total_utility = 0.0
    for step in range(m):
        if MF > 0.0:
            cumulative = 0.0
            previous_served = 0.0
            for i in range(m):
                stock = yb[i]
                cumulative = cumulative + stock
                served = fw * fm1 * (1.0 - fr1 ** cumulative)
                served = served + (1.0 - fw) * fm2 * (1.0 - fr2 ** cumulative)
                use = future_scale * (served - previous_served)
                if use < 0.0:
                    use = 0.0
                if use > stock:
                    use = stock
                yb[i] = stock - use
                total_utility = total_utility + use
                previous_served = served

        if ML > 0.0:
            cumulative = 0.0
            previous_served = 0.0
            for k in range(m):
                i = m - 1 - k
                stock = yb[i]
                cumulative = cumulative + stock
                served = lw * lm1 * (1.0 - lr1 ** cumulative)
                served = served + (1.0 - lw) * lm2 * (1.0 - lr2 ** cumulative)
                use = future_scale * (served - previous_served)
                if use < 0.0:
                    use = 0.0
                if use > stock:
                    use = stock
                yb[i] = stock - use
                total_utility = total_utility + use
                previous_served = served

        for i in range(m - 1):
            yb[i] = yb[i + 1]
        yb[m - 1] = 0.0

    extra_utility = total_utility - fifo_utility
    if extra_utility < 0.0:
        extra_utility = 0.0

    effective_stock = fifo_credit * fifo_utility + lifo_credit * extra_utility
    order = S - effective_stock

    if order != order:
        order = 0.0
    if order < 0.0:
        order = 0.0
    if order > 1000000.0:
        order = 1000000.0
    return float(order)
