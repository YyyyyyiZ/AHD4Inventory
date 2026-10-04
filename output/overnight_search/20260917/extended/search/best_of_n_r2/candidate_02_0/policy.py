def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    C = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    B = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.0}
    R = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":2.0}
    G = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.0}
    SM = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":0.95}

    m = len(age)
    lp = len(pipeline)
    x = [0.0] * m
    direct_effective = 0.0

    for i in range(m):
        x[i] = age[i]
        z = (i + 1.0) / m
        weight = B + (1.0 - B) * (z ** A)
        direct_effective = direct_effective + age[i] * weight

    for j in range(lp):
        direct_effective = direct_effective + pipeline[j]

    mf = f * mu
    vf = f * (mu * cv) ** 2
    fifo_active = mf > 0.0
    fw = 0.0
    fr1 = 0.0
    fr2 = 0.0

    if fifo_active:
        fa = vf / (mf * mf) - 1.0 / mf
        fdisc = fa * fa - 1.0
        if fdisc < 0.0:
            fdisc = 0.0
        fsqrt = fdisc ** 0.5
        fb = 1.0 + fa + fsqrt
        fc = 1.0 + fa - fsqrt
        fw = 1.0 / fb
        fp1 = 2.0 / (2.0 + mf * fb)
        fp2 = 2.0 / (2.0 + mf * fc)
        fr1 = 1.0 - fp1
        fr2 = 1.0 - fp2

    ml = (1.0 - f) * mu
    vl = (1.0 - f) * (mu * cv) ** 2
    lifo_active = ml > 0.0
    lw = 0.0
    lr1 = 0.0
    lr2 = 0.0

    if lifo_active:
        la = vl / (ml * ml) - 1.0 / ml
        ldisc = la * la - 1.0
        if ldisc < 0.0:
            ldisc = 0.0
        lsqrt = ldisc ** 0.5
        lb = 1.0 + la + lsqrt
        lc = 1.0 + la - lsqrt
        lw = 1.0 / lb
        lp1 = 2.0 / (2.0 + ml * lb)
        lp2 = 2.0 / (2.0 + ml * lc)
        lr1 = 1.0 - lp1
        lr2 = 1.0 - lp2

    expired = 0.0

    for t in range(L):
        if fifo_active:
            cumulative = 0.0
            previous_expected = 0.0
            for i in range(m):
                original = x[i]
                cumulative = cumulative + original
                n = int(cumulative)
                fraction = cumulative - n
                e1 = fr1 * (1.0 - fr1 ** n) / (1.0 - fr1)
                e1 = e1 + fraction * fr1 ** (n + 1)
                e2 = fr2 * (1.0 - fr2 ** n) / (1.0 - fr2)
                e2 = e2 + fraction * fr2 ** (n + 1)
                expected = fw * e1 + (1.0 - fw) * e2
                take = K * (expected - previous_expected)
                if take < 0.0:
                    take = 0.0
                if take > original:
                    take = original
                x[i] = original - take
                previous_expected = expected

        if lifo_active:
            cumulative = 0.0
            previous_expected = 0.0
            for h in range(m):
                i = m - 1 - h
                original = x[i]
                cumulative = cumulative + original
                n = int(cumulative)
                fraction = cumulative - n
                e1 = lr1 * (1.0 - lr1 ** n) / (1.0 - lr1)
                e1 = e1 + fraction * lr1 ** (n + 1)
                e2 = lr2 * (1.0 - lr2 ** n) / (1.0 - lr2)
                e2 = e2 + fraction * lr2 ** (n + 1)
                expected = lw * e1 + (1.0 - lw) * e2
                take = K * (expected - previous_expected)
                if take < 0.0:
                    take = 0.0
                if take > original:
                    take = original
                x[i] = original - take
                previous_expected = expected

        expired = expired + x[0]

        for i in range(m - 1):
            x[i] = x[i + 1]

        arrival = 0.0
        if t < lp:
            arrival = pipeline[t]
        x[m - 1] = arrival

    projected_effective = 0.0
    for i in range(m):
        z = (i + 1.0) / m
        weight = B + (1.0 - B) * (z ** A)
        projected_effective = projected_effective + x[i] * weight

    effective = (1.0 - G) * direct_effective
    effective = effective + G * (projected_effective + R * expired)
    raw = S - effective

    last_order = 0.0
    if lp > 0:
        last_order = pipeline[lp - 1]

    q = (1.0 - SM) * raw + SM * last_order
    if q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return q
