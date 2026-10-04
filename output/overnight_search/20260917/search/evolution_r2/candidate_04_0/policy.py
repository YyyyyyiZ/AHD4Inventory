def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    D = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.2,"max":1.8}
    T = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":1.5}
    A = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":8.0}
    W0 = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    B = 0.01 # OPT_PARAM: {"type":"float","initial":0.01,"min":0.0,"max":0.15}
    U = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.1,"max":0.9}

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
            mcf = mf / rhof
            secf = (vf + mf * mf) / rhof
            vcf = max(0.0, secf - mcf * mcf)
            deltaf = max(0.000001, mcf - 1.0)
            alphaf = vcf / (vcf + deltaf * deltaf)
            highf = mcf + vcf / deltaf
            lowf = max(0.0, mcf + T * (1.0 - mcf))
            tailf = max(0.0, mcf + T * (highf - mcf))
            fprob[0] = p0f
            fprob[1] = rhof * alphaf
            fprob[2] = rhof * (1.0 - alphaf)
            fdem[1] = D * lowf
            fdem[2] = D * tailf

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
            mcl = ml / rhol
            secl = (vl + ml * ml) / rhol
            vcl = max(0.0, secl - mcl * mcl)
            deltal = max(0.000001, mcl - 1.0)
            alphal = vcl / (vcl + deltal * deltal)
            highl = mcl + vcl / deltal
            lowl = max(0.0, mcl + T * (1.0 - mcl))
            taill = max(0.0, mcl + T * (highl - mcl))
            lprob[0] = p0l
            lprob[1] = rhol * alphal
            lprob[2] = rhol * (1.0 - alphal)
            ldem[1] = D * lowl
            ldem[2] = D * taill

    scenarios = 3 ** (2 * L)
    gaps = [0.0] * scenarios
    probabilities = [0.0] * scenarios
    mean_gap = 0.0

    for s in range(scenarios):
        x = [0.0] * m
        for i in range(m):
            x[i] = max(0.0, age[i])

        code = s
        probability = 1.0

        for t in range(L):
            if t > 0 and t - 1 < len(pipeline):
                x[m - 1] = x[m - 1] + max(0.0, pipeline[t - 1])

            fs = code % 3
            code = code // 3
            ls = code % 3
            code = code // 3
            probability = probability * fprob[fs] * lprob[ls]

            remaining = fdem[fs]
            for i in range(m):
                take = min(x[i], remaining)
                x[i] = x[i] - take
                remaining = remaining - take

            remaining = ldem[ls]
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

        effective = effective / (1.0 + B * effective)
        gap = S - K * effective
        gaps[s] = gap
        probabilities[s] = probability
        mean_gap = mean_gap + probability * gap

    raw_order = mean_gap
    for iteration in range(6):
        numerator = 0.0
        denominator = 0.0
        for s in range(scenarios):
            if gaps[s] > raw_order:
                risk_weight = U
            else:
                risk_weight = 1.0 - U
            joint_weight = probabilities[s] * risk_weight
            numerator = numerator + joint_weight * gaps[s]
            denominator = denominator + joint_weight
        if denominator > 0.0:
            raw_order = numerator / denominator

    return max(0.0, min(C, raw_order))
