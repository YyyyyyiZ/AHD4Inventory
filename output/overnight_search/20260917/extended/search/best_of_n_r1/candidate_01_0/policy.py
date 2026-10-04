def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 13.5 # OPT_PARAM: {"type":"float","initial":13.5,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    W0 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.5}
    W1 = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":1.5}
    W2 = 0.82 # OPT_PARAM: {"type":"float","initial":0.82,"min":0.0,"max":1.5}
    W3 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.5}
    H = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.0,"max":2.0}
    D = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.5}

    m = len(age)
    age_total = 0.0
    effective = 0.0
    scale = mu
    if scale <= 0.0:
        scale = 1.0

    for i in range(m):
        x = age[i]
        age_total = age_total + x
        r = (i + 1.0) / m
        z = 3.0 * r
        if z <= 1.0:
            w = W0 + (W1 - W0) * z
        elif z <= 2.0:
            w = W1 + (W2 - W1) * (z - 1.0)
        else:
            w = W2 + (W3 - W2) * (z - 2.0)
        denom = 1.0 + H * (1.0 - r) * x / scale
        effective = effective + w * x / denom

    pipe_total = 0.0
    for j in range(len(pipeline)):
        pipe_total = pipe_total + pipeline[j]

    mf = f * mu
    ml = (1.0 - f) * mu

    if mf > 0.0:
        vf = f * (mu * cv) * (mu * cv)
        af = vf / (mf * mf) - 1.0 / mf
        sf = (af * af - 1.0) ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        mixf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2
    else:
        mixf = 0.0
        pf1 = 1.0
        pf2 = 1.0
        rf1 = 0.0
        rf2 = 0.0

    if ml > 0.0:
        vl = (1.0 - f) * (mu * cv) * (mu * cv)
        al = vl / (ml * ml) - 1.0 / ml
        sl = (al * al - 1.0) ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        mixl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2
    else:
        mixl = 0.0
        pl1 = 1.0
        pl2 = 1.0
        rl1 = 0.0
        rl2 = 0.0

    projected = [0.0] * m
    for i in range(m):
        projected[i] = age[i]

    for h in range(L):
        total = 0.0
        for i in range(m):
            total = total + projected[i]

        served = 0.0
        if mf > 0.0 and total > 0.0:
            n = int(total)
            frac = total - n
            powf1 = rf1 ** n
            powf2 = rf2 ** n
            ef1 = rf1 * (1.0 - powf1) / pf1 + frac * powf1 * rf1
            ef2 = rf2 * (1.0 - powf2) / pf2 + frac * powf2 * rf2
            served = mixf * ef1 + (1.0 - mixf) * ef2

        remaining = served
        for i in range(m):
            take = projected[i]
            if take > remaining:
                take = remaining
            projected[i] = projected[i] - take
            remaining = remaining - take

        total = 0.0
        for i in range(m):
            total = total + projected[i]

        served = 0.0
        if ml > 0.0 and total > 0.0:
            n = int(total)
            frac = total - n
            powl1 = rl1 ** n
            powl2 = rl2 ** n
            el1 = rl1 * (1.0 - powl1) / pl1 + frac * powl1 * rl1
            el2 = rl2 * (1.0 - powl2) / pl2 + frac * powl2 * rl2
            served = mixl * el1 + (1.0 - mixl) * el2

        remaining = served
        for k in range(m):
            i = m - 1 - k
            take = projected[i]
            if take > remaining:
                take = remaining
            projected[i] = projected[i] - take
            remaining = remaining - take

        for i in range(m - 1):
            projected[i] = projected[i + 1]
        if m > 0:
            projected[m - 1] = 0.0

        if h < L - 1 and h < len(pipeline) and m > 0:
            projected[m - 1] = projected[m - 1] + pipeline[h]

    residual = 0.0
    for i in range(m):
        residual = residual + projected[i]

    depletion = age_total + pipe_total - residual
    if depletion < 0.0:
        depletion = 0.0

    q = S - effective - P * pipe_total + D * depletion
    if q != q or q <= 0.0:
        return 0.0
    if q > C:
        q = C
    return float(q)
