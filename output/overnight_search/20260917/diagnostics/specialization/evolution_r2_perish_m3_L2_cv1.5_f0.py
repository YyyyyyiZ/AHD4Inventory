def compute_order_amount(age, pipeline, _opt_values):
    mu = 4.0
    cv = 1.5
    f = 0.0
    L = 2
    S = _opt_values[0]
    C = _opt_values[1]
    D = _opt_values[2]
    H = _opt_values[3]
    ALPHA = _opt_values[4]
    A = _opt_values[5]
    W0 = _opt_values[6]
    K = _opt_values[7]
    R = _opt_values[8]
    G = _opt_values[9]
    m = len(age)
    mf = f * mu
    ml = (1.0 - f) * mu
    fprob = [1.0, 0.0, 0.0]
    fdem = [0.0, 0.0, 0.0]
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
            secondf = (vf + mf * mf) / rhof
            varcondf = max(0.0, secondf - condf * condf)
            sdcondf = varcondf ** 0.5
            ratio_low = ((1.0 - ALPHA) / ALPHA) ** 0.5
            lowf = max(0.0, condf - H * sdcondf * ratio_low)
            highf = max(0.0, (condf - ALPHA * lowf) / (1.0 - ALPHA))
            fprob[0] = 1.0 - rhof
            fprob[1] = rhof * ALPHA
            fprob[2] = rhof * (1.0 - ALPHA)
            fdem[1] = D * lowf
            fdem[2] = D * highf
    lprob = [1.0, 0.0, 0.0]
    ldem = [0.0, 0.0, 0.0]
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
            secondl = (vl + ml * ml) / rhol
            varcondl = max(0.0, secondl - condl * condl)
            sdcondl = varcondl ** 0.5
            ratio_low = ((1.0 - ALPHA) / ALPHA) ** 0.5
            lowl = max(0.0, condl - H * sdcondl * ratio_low)
            highl = max(0.0, (condl - ALPHA * lowl) / (1.0 - ALPHA))
            lprob[0] = 1.0 - rhol
            lprob[1] = rhol * ALPHA
            lprob[2] = rhol * (1.0 - ALPHA)
            ldem[1] = D * lowl
            ldem[2] = D * highl
    mean_credit = 0.0
    second_credit = 0.0
    mean_gap = 0.0
    scenarios = 3 ** (2 * L)
    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = age[i]
        code = s
        probability = 1.0
        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + pipeline[t - 1]
            fifo_state = code % 3
            code = code // 3
            lifo_state = code % 3
            code = code // 3
            probability = probability * fprob[fifo_state] * lprob[lifo_state]
            if probability > 0.0:
                remaining = fdem[fifo_state]
                for i in range(m):
                    take = min(x[i], remaining)
                    x[i] = x[i] - take
                    remaining = remaining - take
                remaining = ldem[lifo_state]
                for j in range(m):
                    i = m - 1 - j
                    take = min(x[i], remaining)
                    x[i] = x[i] - take
                    remaining = remaining - take
            for i in range(m - 1):
                x[i] = x[i + 1]
            x[m - 1] = 0.0
        if probability > 0.0:
            effective = 0.0
            for i in range(m):
                relative_life = (i + 1.0) / m
                weight = W0 + (1.0 - W0) * relative_life ** A
                effective = effective + weight * x[i]
            credit = K * effective
            gap = max(0.0, S - credit)
            mean_credit = mean_credit + probability * credit
            second_credit = second_credit + probability * credit * credit
            mean_gap = mean_gap + probability * gap
    variance_credit = max(0.0, second_credit - mean_credit * mean_credit)
    deviation_credit = variance_credit ** 0.5
    linear_gap = S - mean_credit
    convex_adjustment = max(0.0, mean_gap - max(0.0, linear_gap))
    raw_order = linear_gap + G * convex_adjustment - R * deviation_credit
    return max(0.0, min(C, raw_order))