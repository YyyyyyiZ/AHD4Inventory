def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    W = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":1.0}
    A = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":4.0}
    KF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    KL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}

    m = len(age)
    stock = [0.0] * m
    for i in range(m):
        stock[i] = max(0.0, float(age[i]))

    MF = f * mu
    ML = (1.0 - f) * mu
    total_variance = (mu * cv) ** 2

    if MF > 0.0:
        VF = f * total_variance
        af = VF / (MF * MF) - 1.0 / MF
        af = max(1.0, af)
        rootf = max(0.0, af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + MF * bf)
        pf2 = 2.0 / (2.0 + MF * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2
    else:
        wf = 0.0
        pf1 = 1.0
        pf2 = 1.0
        rf1 = 0.0
        rf2 = 0.0

    if ML > 0.0:
        VL = (1.0 - f) * total_variance
        al = VL / (ML * ML) - 1.0 / ML
        al = max(1.0, al)
        rootl = max(0.0, al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ML * bl)
        pl2 = 2.0 / (2.0 + ML * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2
    else:
        wl = 0.0
        pl1 = 1.0
        pl2 = 1.0
        rl1 = 0.0
        rl2 = 0.0

    for step in range(L):
        if MF > 0.0:
            cumulative = 0.0
            for i in range(m):
                quantity = max(0.0, stock[i])
                lower = cumulative
                upper = cumulative + quantity

                n0 = int(lower) + 1
                e01 = (n0 - lower) * (rf1 ** n0) + (rf1 ** (n0 + 1)) / pf1
                e02 = (n0 - lower) * (rf2 ** n0) + (rf2 ** (n0 + 1)) / pf2
                excess0 = wf * e01 + (1.0 - wf) * e02

                n1 = int(upper) + 1
                e11 = (n1 - upper) * (rf1 ** n1) + (rf1 ** (n1 + 1)) / pf1
                e12 = (n1 - upper) * (rf2 ** n1) + (rf2 ** (n1 + 1)) / pf2
                excess1 = wf * e11 + (1.0 - wf) * e12

                consumed = KF * max(0.0, excess0 - excess1)
                consumed = min(quantity, consumed)
                stock[i] = quantity - consumed
                cumulative = upper

        if ML > 0.0:
            cumulative = 0.0
            for z in range(m):
                i = m - 1 - z
                quantity = max(0.0, stock[i])
                lower = cumulative
                upper = cumulative + quantity

                n0 = int(lower) + 1
                e01 = (n0 - lower) * (rl1 ** n0) + (rl1 ** (n0 + 1)) / pl1
                e02 = (n0 - lower) * (rl2 ** n0) + (rl2 ** (n0 + 1)) / pl2
                excess0 = wl * e01 + (1.0 - wl) * e02

                n1 = int(upper) + 1
                e11 = (n1 - upper) * (rl1 ** n1) + (rl1 ** (n1 + 1)) / pl1
                e12 = (n1 - upper) * (rl2 ** n1) + (rl2 ** (n1 + 1)) / pl2
                excess1 = wl * e11 + (1.0 - wl) * e12

                consumed = KL * max(0.0, excess0 - excess1)
                consumed = min(quantity, consumed)
                stock[i] = quantity - consumed
                cumulative = upper

        for i in range(m - 1):
            stock[i] = stock[i + 1]
        if m > 0:
            stock[m - 1] = 0.0
            if step < len(pipeline):
                stock[m - 1] = max(0.0, float(pipeline[step]))

    effective = 0.0
    if m > 0:
        for i in range(m):
            relative_life = (i + 1.0) / m
            weight = W + (1.0 - W) * (relative_life ** A)
            effective = effective + weight * max(0.0, stock[i])

    order = S - effective
    order = max(0.0, min(C, order))
    return float(order)
