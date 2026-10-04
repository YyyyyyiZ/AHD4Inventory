def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    W1 = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":2.0}
    W2 = 0.60 # OPT_PARAM: {"type":"float","initial":0.60,"min":0.0,"max":2.0}
    W3 = 0.82 # OPT_PARAM: {"type":"float","initial":0.82,"min":0.0,"max":2.0}
    W4 = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":2.0}
    KF = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":2.0}
    KL = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":2.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        v = float(age[i])
        if v < 0.0:
            v = 0.0
        x[i] = v

    if f > 0.0:
        MF = f * mu
        VF = f * (mu * cv) * (mu * cv)
        aF = VF / (MF * MF) - 1.0 / MF
        rootF = (aF * aF - 1.0) ** 0.5
        bF = 1.0 + aF + rootF
        cF = 1.0 + aF - rootF
        mixF = 1.0 / bF
        pF1 = 2.0 / (2.0 + MF * bF)
        pF2 = 2.0 / (2.0 + MF * cF)
        rF1 = 1.0 - pF1
        rF2 = 1.0 - pF2

    gL = 1.0 - f
    if gL > 0.0:
        ML = gL * mu
        VL = gL * (mu * cv) * (mu * cv)
        aL = VL / (ML * ML) - 1.0 / ML
        rootL = (aL * aL - 1.0) ** 0.5
        bL = 1.0 + aL + rootL
        cL = 1.0 + aL - rootL
        mixL = 1.0 / bL
        pL1 = 2.0 / (2.0 + ML * bL)
        pL2 = 2.0 / (2.0 + ML * cL)
        rL1 = 1.0 - pL1
        rL2 = 1.0 - pL2

    for t in range(L):
        if f > 0.0:
            y = [0.0] * m
            cumulative = 0.0
            previous_remaining = 0.0
            for i in range(m):
                cumulative = cumulative + x[i]
                if cumulative > 0.0:
                    truncated1 = rF1 * (1.0 - rF1 ** cumulative) / pF1
                    truncated2 = rF2 * (1.0 - rF2 ** cumulative) / pF2
                    remaining = cumulative - mixF * truncated1 - (1.0 - mixF) * truncated2
                    if remaining < 0.0:
                        remaining = 0.0
                    if remaining > cumulative:
                        remaining = cumulative
                else:
                    remaining = 0.0
                exact_cohort = remaining - previous_remaining
                calibrated = x[i] + KF * (exact_cohort - x[i])
                if calibrated < 0.0:
                    calibrated = 0.0
                if calibrated > x[i]:
                    calibrated = x[i]
                y[i] = calibrated
                previous_remaining = remaining
            x = y

        if gL > 0.0:
            y = [0.0] * m
            cumulative = 0.0
            previous_remaining = 0.0
            for k in range(m):
                i = m - 1 - k
                cumulative = cumulative + x[i]
                if cumulative > 0.0:
                    truncated1 = rL1 * (1.0 - rL1 ** cumulative) / pL1
                    truncated2 = rL2 * (1.0 - rL2 ** cumulative) / pL2
                    remaining = cumulative - mixL * truncated1 - (1.0 - mixL) * truncated2
                    if remaining < 0.0:
                        remaining = 0.0
                    if remaining > cumulative:
                        remaining = cumulative
                else:
                    remaining = 0.0
                exact_cohort = remaining - previous_remaining
                calibrated = x[i] + KL * (exact_cohort - x[i])
                if calibrated < 0.0:
                    calibrated = 0.0
                if calibrated > x[i]:
                    calibrated = x[i]
                y[i] = calibrated
                previous_remaining = remaining
            x = y

        for i in range(m - 1):
            x[i] = x[i + 1]
        if m > 0:
            x[m - 1] = 0.0
            if t < len(pipeline):
                arrival = float(pipeline[t])
                if arrival > 0.0:
                    x[m - 1] = arrival

    effective_inventory = 0.0
    for i in range(m):
        if i == 0:
            weight = W1
        elif i == 1:
            weight = W2
        elif i == 2:
            weight = W3
        else:
            weight = W4
        effective_inventory = effective_inventory + weight * x[i]

    q = S - effective_inventory
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 60.0:
        q = 60.0
    return float(q)
