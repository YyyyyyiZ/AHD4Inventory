def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    B = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    W0 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":1.5}
    WSTEP = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":0.8}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        v = float(age[i])
        if v < 0.0:
            v = 0.0
        x[i] = v

    mf = float(f) * float(mu)
    ml = (1.0 - float(f)) * float(mu)
    variance_scale = (float(mu) * float(cv)) ** 2

    if mf > 0.0:
        vf = float(f) * variance_scale
        af = vf / (mf * mf) - 1.0 / mf
        if af < 1.0:
            af = 1.0
        rootf = (af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    if ml > 0.0:
        vl = (1.0 - float(f)) * variance_scale
        al = vl / (ml * ml) - 1.0 / ml
        if al < 1.0:
            al = 1.0
        rootl = (al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    for period in range(int(L)):
        if mf > 0.0:
            y = [0.0] * m
            before = 0.0
            for i in range(m):
                end = before + x[i]

                nb = int(before)
                fb = before - float(nb)
                eb1 = rf1 * (1.0 - rf1 ** nb) / pf1 + fb * rf1 ** (nb + 1)
                eb2 = rf2 * (1.0 - rf2 ** nb) / pf2 + fb * rf2 ** (nb + 1)
                eb = wf * eb1 + (1.0 - wf) * eb2

                ne = int(end)
                fe = end - float(ne)
                ee1 = rf1 * (1.0 - rf1 ** ne) / pf1 + fe * rf1 ** (ne + 1)
                ee2 = rf2 * (1.0 - rf2 ** ne) / pf2 + fe * rf2 ** (ne + 1)
                ee = wf * ee1 + (1.0 - wf) * ee2

                exact_remove = ee - eb
                fluid_end = end
                if fluid_end > mf:
                    fluid_end = mf
                fluid_before = before
                if fluid_before > mf:
                    fluid_before = mf
                fluid_remove = fluid_end - fluid_before

                remove = K * ((1.0 - B) * exact_remove + B * fluid_remove)
                if remove < 0.0:
                    remove = 0.0
                if remove > x[i]:
                    remove = x[i]
                y[i] = x[i] - remove
                before = end
            x = y

        if ml > 0.0:
            y = [0.0] * m
            before = 0.0
            for k in range(m):
                i = m - 1 - k
                end = before + x[i]

                nb = int(before)
                fb = before - float(nb)
                eb1 = rl1 * (1.0 - rl1 ** nb) / pl1 + fb * rl1 ** (nb + 1)
                eb2 = rl2 * (1.0 - rl2 ** nb) / pl2 + fb * rl2 ** (nb + 1)
                eb = wl * eb1 + (1.0 - wl) * eb2

                ne = int(end)
                fe = end - float(ne)
                ee1 = rl1 * (1.0 - rl1 ** ne) / pl1 + fe * rl1 ** (ne + 1)
                ee2 = rl2 * (1.0 - rl2 ** ne) / pl2 + fe * rl2 ** (ne + 1)
                ee = wl * ee1 + (1.0 - wl) * ee2

                exact_remove = ee - eb
                fluid_end = end
                if fluid_end > ml:
                    fluid_end = ml
                fluid_before = before
                if fluid_before > ml:
                    fluid_before = ml
                fluid_remove = fluid_end - fluid_before

                remove = K * ((1.0 - B) * exact_remove + B * fluid_remove)
                if remove < 0.0:
                    remove = 0.0
                if remove > x[i]:
                    remove = x[i]
                y[i] = x[i] - remove
                before = end
            x = y

        y = [0.0] * m
        for i in range(m - 1):
            y[i] = x[i + 1]
        if period < len(pipeline):
            arrival = float(pipeline[period])
            if arrival < 0.0:
                arrival = 0.0
            y[m - 1] = arrival
        x = y

    effective_stock = 0.0
    for i in range(m):
        weight = W0 + WSTEP * float(i)
        if weight > 1.5:
            weight = 1.5
        effective_stock = effective_stock + weight * x[i]

    q = S - effective_stock
    if not (q >= 0.0):
        q = 0.0
    return q
