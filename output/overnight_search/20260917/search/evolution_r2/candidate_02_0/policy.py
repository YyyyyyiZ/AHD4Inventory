def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    D = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.3,"max":1.8}
    A = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":8.0}
    W0 = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    R = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}
    B = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}

    m = len(age)
    mf = f * mu
    ml = (1.0 - f) * mu

    fprob = [1.0, 0.0, 0.0, 0.0]
    fdemand = [0.0, 0.0, 0.0, 0.0]

    if mf > 0.0:
        vf = f * (mu * cv) * (mu * cv)
        af = vf / (mf * mf) - 1.0 / mf
        sf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

        fprob[0] = wf * pf1 + (1.0 - wf) * pf2
        fmom1 = 0.0
        fmom2 = 0.0

        for k in range(1, 7):
            pk = wf * pf1 * (rf1 ** k) + (1.0 - wf) * pf2 * (rf2 ** k)
            if k <= 2:
                fprob[1] = fprob[1] + pk
                fmom1 = fmom1 + k * pk
            else:
                fprob[2] = fprob[2] + pk
                fmom2 = fmom2 + k * pk

        ftail1 = wf * (rf1 ** 7)
        ftail2 = (1.0 - wf) * (rf2 ** 7)
        fprob[3] = ftail1 + ftail2
        ftailmom = ftail1 * (7.0 + rf1 / pf1)
        ftailmom = ftailmom + ftail2 * (7.0 + rf2 / pf2)

        if fprob[1] > 0.0:
            fdemand[1] = fmom1 / fprob[1]
        if fprob[2] > 0.0:
            fdemand[2] = fmom2 / fprob[2]
        if fprob[3] > 0.0:
            fdemand[3] = ftailmom / fprob[3]

    lprob = [1.0, 0.0, 0.0, 0.0]
    ldemand = [0.0, 0.0, 0.0, 0.0]

    if ml > 0.0:
        vl = (1.0 - f) * (mu * cv) * (mu * cv)
        al = vl / (ml * ml) - 1.0 / ml
        sl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

        lprob[0] = wl * pl1 + (1.0 - wl) * pl2
        lmom1 = 0.0
        lmom2 = 0.0

        for k in range(1, 7):
            pk = wl * pl1 * (rl1 ** k) + (1.0 - wl) * pl2 * (rl2 ** k)
            if k <= 2:
                lprob[1] = lprob[1] + pk
                lmom1 = lmom1 + k * pk
            else:
                lprob[2] = lprob[2] + pk
                lmom2 = lmom2 + k * pk

        ltail1 = wl * (rl1 ** 7)
        ltail2 = (1.0 - wl) * (rl2 ** 7)
        lprob[3] = ltail1 + ltail2
        ltailmom = ltail1 * (7.0 + rl1 / pl1)
        ltailmom = ltailmom + ltail2 * (7.0 + rl2 / pl2)

        if lprob[1] > 0.0:
            ldemand[1] = lmom1 / lprob[1]
        if lprob[2] > 0.0:
            ldemand[2] = lmom2 / lprob[2]
        if lprob[3] > 0.0:
            ldemand[3] = ltailmom / lprob[3]

    mean_effective = 0.0
    second_effective = 0.0
    expected_shortfall = 0.0
    scenarios = 4 ** (2 * L)

    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = age[i]

        code = s
        probability = 1.0

        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + pipeline[t - 1]

            fifo_state = code % 4
            code = code // 4
            lifo_state = code % 4
            code = code // 4

            probability = probability * fprob[fifo_state]
            probability = probability * lprob[lifo_state]

            if probability > 0.0:
                remaining = D * fdemand[fifo_state]
                for i in range(m):
                    take = min(x[i], remaining)
                    x[i] = x[i] - take
                    remaining = remaining - take

                remaining = D * ldemand[lifo_state]
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
                weight = W0 + (1.0 - W0) * (relative_life ** A)
                effective = effective + weight * x[i]

            mean_effective = mean_effective + probability * effective
            second_effective = second_effective + probability * effective * effective
            deficit = max(0.0, S - K * effective)
            expected_shortfall = expected_shortfall + probability * deficit

    variance_effective = max(
        0.0, second_effective - mean_effective * mean_effective
    )
    deviation_effective = variance_effective ** 0.5
    linear_order = S - K * mean_effective
    raw_order = (1.0 - B) * linear_order + B * expected_shortfall
    raw_order = raw_order + R * deviation_effective

    return max(0.0, min(C, raw_order))
