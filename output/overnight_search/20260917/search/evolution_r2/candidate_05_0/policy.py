def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    DF = 0.85 # OPT_PARAM: {"type":"float","initial":0.85,"min":0.2,"max":2.0}
    DL = 0.85 # OPT_PARAM: {"type":"float","initial":0.85,"min":0.2,"max":2.0}
    H = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.0}
    WOLD = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":2.0}
    WMID = 0.4 # OPT_PARAM: {"type":"float","initial":0.4,"min":0.0,"max":2.0}
    WNEW = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    G = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.5}
    R = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":2.0}

    m = len(age)
    mf = f * mu
    ml = (1.0 - f) * mu

    fprob = [1.0, 0.0, 0.0]
    fp = [1.0, 1.0, 1.0]
    if mf > 0.0:
        vf = f * (mu * cv) * (mu * cv)
        af = vf / (mf * mf) - 1.0 / mf
        sf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        fprob[0] = wf * pf1 + (1.0 - wf) * pf2
        fprob[1] = wf * (1.0 - pf1)
        fprob[2] = (1.0 - wf) * (1.0 - pf2)
        fp[1] = pf1
        fp[2] = pf2

    lprob = [1.0, 0.0, 0.0]
    lp = [1.0, 1.0, 1.0]
    if ml > 0.0:
        vl = (1.0 - f) * (mu * cv) * (mu * cv)
        al = vl / (ml * ml) - 1.0 / ml
        sl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        lprob[0] = wl * pl1 + (1.0 - wl) * pl2
        lprob[1] = wl * (1.0 - pl1)
        lprob[2] = (1.0 - wl) * (1.0 - pl2)
        lp[1] = pl1
        lp[2] = pl2

    mean_credit = 0.0
    second_credit = 0.0
    mean_gap = 0.0
    scenarios = 3 ** (2 * L)

    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = max(0.0, age[i])

        probability = 1.0
        code = s

        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + max(0.0, pipeline[t - 1])

            fifo_state = code % 3
            code = code // 3
            lifo_state = code % 3
            code = code // 3

            probability = probability * fprob[fifo_state] * lprob[lifo_state]

            if fifo_state > 0:
                pnow = fp[fifo_state]
                decay = 1.0 - pnow
                base = [0.0] * m
                deterministic = [0.0] * m
                analytic = [0.0] * m
                stock = 0.0

                for i in range(m):
                    base[i] = x[i]
                    deterministic[i] = x[i]
                    stock = stock + x[i]

                demand = DF * (1.0 - decay ** stock) / pnow
                remaining = demand
                for i in range(m):
                    take = min(deterministic[i], remaining)
                    deterministic[i] = deterministic[i] - take
                    remaining = remaining - take

                cumulative = 0.0
                for i in range(m):
                    quantity = base[i]
                    expected_take = DF * (decay ** cumulative) * (
                        1.0 - decay ** quantity
                    ) / pnow
                    expected_take = min(quantity, max(0.0, expected_take))
                    analytic[i] = quantity - expected_take
                    cumulative = cumulative + quantity

                for i in range(m):
                    x[i] = (1.0 - H) * deterministic[i] + H * analytic[i]

            if lifo_state > 0:
                pnow = lp[lifo_state]
                decay = 1.0 - pnow
                base = [0.0] * m
                deterministic = [0.0] * m
                analytic = [0.0] * m
                stock = 0.0

                for i in range(m):
                    base[i] = x[i]
                    deterministic[i] = x[i]
                    stock = stock + x[i]

                demand = DL * (1.0 - decay ** stock) / pnow
                remaining = demand
                for j in range(m):
                    i = m - 1 - j
                    take = min(deterministic[i], remaining)
                    deterministic[i] = deterministic[i] - take
                    remaining = remaining - take

                cumulative = 0.0
                for j in range(m):
                    i = m - 1 - j
                    quantity = base[i]
                    expected_take = DL * (decay ** cumulative) * (
                        1.0 - decay ** quantity
                    ) / pnow
                    expected_take = min(quantity, max(0.0, expected_take))
                    analytic[i] = quantity - expected_take
                    cumulative = cumulative + quantity

                for i in range(m):
                    x[i] = (1.0 - H) * deterministic[i] + H * analytic[i]

            for i in range(m - 1):
                x[i] = x[i + 1]
            x[m - 1] = 0.0

        if probability > 0.0:
            credit = 0.0
            for i in range(m):
                u = (i + 1.0) / m
                one_minus_u = 1.0 - u
                weight = (
                    WOLD * one_minus_u * one_minus_u
                    + 2.0 * WMID * u * one_minus_u
                    + WNEW * u * u
                )
                credit = credit + weight * x[i]

            gap = max(0.0, S - credit)
            mean_credit = mean_credit + probability * credit
            second_credit = second_credit + probability * credit * credit
            mean_gap = mean_gap + probability * gap

    variance_credit = max(
        0.0, second_credit - mean_credit * mean_credit
    )
    deviation_credit = variance_credit ** 0.5
    linear_gap = max(0.0, S - mean_credit)
    raw_order = (
        linear_gap
        + G * (mean_gap - linear_gap)
        - R * deviation_credit
    )

    return max(0.0, min(C, raw_order))
