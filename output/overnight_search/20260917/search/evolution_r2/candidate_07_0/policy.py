def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    D = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.4,"max":1.8}
    A = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":8.0}
    WOLD = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.5}
    WFRESH = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":2.0}
    Q = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-0.5,"max":1.0}
    G = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":3.0}
    R = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}

    m = len(age)
    mf = f * mu
    ml = (1.0 - f) * mu

    fprob = [1.0, 0.0, 0.0, 0.0]
    fdem = [0.0, 0.0, 0.0, 0.0]
    nf = 1

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
        p0f = wf * pf1 + (1.0 - wf) * pf2
        rhof = max(0.0, 1.0 - p0f)

        n1f = 0
        n2f = 0
        for k in range(1, 161):
            cumf = (
                wf * (rf1 - rf1 ** (k + 1))
                + (1.0 - wf) * (rf2 - rf2 ** (k + 1))
            )
            if n1f == 0 and cumf >= 0.50 * rhof:
                n1f = k
            if n2f == 0 and cumf >= 0.90 * rhof:
                n2f = k

        if n1f == 0:
            n1f = 160
        if n2f == 0:
            n2f = 160
        if n2f < n1f:
            n2f = n1f

        prob1f = (
            wf * (rf1 - rf1 ** (n1f + 1))
            + (1.0 - wf) * (rf2 - rf2 ** (n1f + 1))
        )
        prob12f = (
            wf * (rf1 - rf1 ** (n2f + 1))
            + (1.0 - wf) * (rf2 - rf2 ** (n2f + 1))
        )

        mom1f = (
            wf
            * rf1
            * (
                1.0
                - (n1f + 1.0) * rf1 ** n1f
                + n1f * rf1 ** (n1f + 1)
            )
            / pf1
            + (1.0 - wf)
            * rf2
            * (
                1.0
                - (n1f + 1.0) * rf2 ** n1f
                + n1f * rf2 ** (n1f + 1)
            )
            / pf2
        )
        mom12f = (
            wf
            * rf1
            * (
                1.0
                - (n2f + 1.0) * rf1 ** n2f
                + n2f * rf1 ** (n2f + 1)
            )
            / pf1
            + (1.0 - wf)
            * rf2
            * (
                1.0
                - (n2f + 1.0) * rf2 ** n2f
                + n2f * rf2 ** (n2f + 1)
            )
            / pf2
        )

        bin1f = max(0.0, prob1f)
        bin2f = max(0.0, prob12f - prob1f)
        bin3f = max(0.0, rhof - prob12f)
        em1f = max(0.0, mom1f)
        em2f = max(0.0, mom12f - mom1f)
        em3f = max(0.0, mf - mom12f)

        fprob[0] = p0f
        fprob[1] = bin1f
        fprob[2] = bin2f
        fprob[3] = bin3f
        if bin1f > 0.0:
            fdem[1] = D * em1f / bin1f
        if bin2f > 0.0:
            fdem[2] = D * em2f / bin2f
        if bin3f > 0.0:
            fdem[3] = D * em3f / bin3f
        nf = 4

    lprob = [1.0, 0.0, 0.0, 0.0]
    ldem = [0.0, 0.0, 0.0, 0.0]
    nl = 1

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
        p0l = wl * pl1 + (1.0 - wl) * pl2
        rhol = max(0.0, 1.0 - p0l)

        n1l = 0
        n2l = 0
        for k in range(1, 161):
            cuml = (
                wl * (rl1 - rl1 ** (k + 1))
                + (1.0 - wl) * (rl2 - rl2 ** (k + 1))
            )
            if n1l == 0 and cuml >= 0.50 * rhol:
                n1l = k
            if n2l == 0 and cuml >= 0.90 * rhol:
                n2l = k

        if n1l == 0:
            n1l = 160
        if n2l == 0:
            n2l = 160
        if n2l < n1l:
            n2l = n1l

        prob1l = (
            wl * (rl1 - rl1 ** (n1l + 1))
            + (1.0 - wl) * (rl2 - rl2 ** (n1l + 1))
        )
        prob12l = (
            wl * (rl1 - rl1 ** (n2l + 1))
            + (1.0 - wl) * (rl2 - rl2 ** (n2l + 1))
        )

        mom1l = (
            wl
            * rl1
            * (
                1.0
                - (n1l + 1.0) * rl1 ** n1l
                + n1l * rl1 ** (n1l + 1)
            )
            / pl1
            + (1.0 - wl)
            * rl2
            * (
                1.0
                - (n1l + 1.0) * rl2 ** n1l
                + n1l * rl2 ** (n1l + 1)
            )
            / pl2
        )
        mom12l = (
            wl
            * rl1
            * (
                1.0
                - (n2l + 1.0) * rl1 ** n2l
                + n2l * rl1 ** (n2l + 1)
            )
            / pl1
            + (1.0 - wl)
            * rl2
            * (
                1.0
                - (n2l + 1.0) * rl2 ** n2l
                + n2l * rl2 ** (n2l + 1)
            )
            / pl2
        )

        bin1l = max(0.0, prob1l)
        bin2l = max(0.0, prob12l - prob1l)
        bin3l = max(0.0, rhol - prob12l)
        em1l = max(0.0, mom1l)
        em2l = max(0.0, mom12l - mom1l)
        em3l = max(0.0, ml - mom12l)

        lprob[0] = p0l
        lprob[1] = bin1l
        lprob[2] = bin2l
        lprob[3] = bin3l
        if bin1l > 0.0:
            ldem[1] = D * em1l / bin1l
        if bin2l > 0.0:
            ldem[2] = D * em2l / bin2l
        if bin3l > 0.0:
            ldem[3] = D * em3l / bin3l
        nl = 4

    mean_credit = 0.0
    second_credit = 0.0
    mean_gap = 0.0
    joint_states = nf * nl
    scenarios = joint_states ** L

    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = max(0.0, age[i])

        code = s
        probability = 1.0

        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + max(0.0, pipeline[t - 1])

            joint_state = code % joint_states
            code = code // joint_states
            fifo_state = joint_state % nf
            lifo_state = joint_state // nf

            probability = (
                probability
                * fprob[fifo_state]
                * lprob[lifo_state]
            )

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
            total = 0.0
            for i in range(m):
                relative_life = (i + 1.0) / m
                weight = WOLD + (WFRESH - WOLD) * (relative_life ** A)
                effective = effective + weight * x[i]
                total = total + x[i]

            congestion_scale = m * mu + 1.0
            credit = effective + Q * total * total / congestion_scale
            gap = max(0.0, S - credit)
            mean_credit = mean_credit + probability * credit
            second_credit = second_credit + probability * credit * credit
            mean_gap = mean_gap + probability * gap

    variance_credit = max(
        0.0, second_credit - mean_credit * mean_credit
    )
    deviation_credit = variance_credit ** 0.5
    linear_gap = S - mean_credit
    convex_adjustment = max(
        0.0, mean_gap - max(0.0, linear_gap)
    )
    raw_order = linear_gap + G * convex_adjustment - R * deviation_credit

    return max(0.0, min(C, raw_order))
