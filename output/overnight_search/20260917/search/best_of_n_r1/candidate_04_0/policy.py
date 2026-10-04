def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    D_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.35,"max":1.8}
    AGE_LINEAR = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-2.0,"max":2.0}
    AGE_CURVE = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":2.0}

    m = len(age)
    state = [0.0 for _ in range(m)]
    for i in range(m):
        value = float(age[i])
        if value < 0.0:
            value = 0.0
        state[i] = value

    mf = float(f) * float(mu)
    vf = float(f) * (float(mu) * float(cv)) ** 2
    ml = (1.0 - float(f)) * float(mu)
    vl = (1.0 - float(f)) * (float(mu) * float(cv)) ** 2

    wf = 0.0
    rf1 = 0.0
    rf2 = 0.0
    if mf > 0.0:
        af = vf / (mf * mf) - 1.0 / mf
        radf = af * af - 1.0
        if radf < 0.0:
            radf = 0.0
        rootf = radf ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        meanf1 = (1.0 - pf1) / pf1
        meanf2 = (1.0 - pf2) / pf2
        sf1 = D_SCALE * meanf1
        sf2 = D_SCALE * meanf2
        rf1 = sf1 / (1.0 + sf1)
        rf2 = sf2 / (1.0 + sf2)

    wl = 0.0
    rl1 = 0.0
    rl2 = 0.0
    if ml > 0.0:
        al = vl / (ml * ml) - 1.0 / ml
        radl = al * al - 1.0
        if radl < 0.0:
            radl = 0.0
        rootl = radl ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        meanl1 = (1.0 - pl1) / pl1
        meanl2 = (1.0 - pl2) / pl2
        sl1 = D_SCALE * meanl1
        sl2 = D_SCALE * meanl2
        rl1 = sl1 / (1.0 + sl1)
        rl2 = sl2 / (1.0 + sl2)

    for step in range(L):
        if step > 0:
            pipe_index = step - 1
            if pipe_index < len(pipeline):
                arrival = float(pipeline[pipe_index])
                if arrival > 0.0:
                    state[m - 1] = state[m - 1] + arrival

        if mf > 0.0:
            after_fifo = [0.0 for _ in range(m)]
            cumulative = 0.0
            previous_left = 0.0
            for i in range(m):
                cumulative = cumulative + state[i]
                n = int(cumulative)
                fraction = cumulative - float(n)
                used1 = rf1 * (1.0 - rf1 ** n) / (1.0 - rf1)
                used1 = used1 + fraction * rf1 ** (n + 1)
                used2 = rf2 * (1.0 - rf2 ** n) / (1.0 - rf2)
                used2 = used2 + fraction * rf2 ** (n + 1)
                expected_left = cumulative - wf * used1 - (1.0 - wf) * used2
                if expected_left < 0.0:
                    expected_left = 0.0
                if expected_left > cumulative:
                    expected_left = cumulative
                cohort_left = expected_left - previous_left
                if cohort_left < 0.0:
                    cohort_left = 0.0
                if cohort_left > state[i]:
                    cohort_left = state[i]
                after_fifo[i] = cohort_left
                previous_left = expected_left
            state = after_fifo

        if ml > 0.0:
            after_lifo = [0.0 for _ in range(m)]
            cumulative = 0.0
            previous_left = 0.0
            for reverse_index in range(m):
                i = m - 1 - reverse_index
                cumulative = cumulative + state[i]
                n = int(cumulative)
                fraction = cumulative - float(n)
                used1 = rl1 * (1.0 - rl1 ** n) / (1.0 - rl1)
                used1 = used1 + fraction * rl1 ** (n + 1)
                used2 = rl2 * (1.0 - rl2 ** n) / (1.0 - rl2)
                used2 = used2 + fraction * rl2 ** (n + 1)
                expected_left = cumulative - wl * used1 - (1.0 - wl) * used2
                if expected_left < 0.0:
                    expected_left = 0.0
                if expected_left > cumulative:
                    expected_left = cumulative
                cohort_left = expected_left - previous_left
                if cohort_left < 0.0:
                    cohort_left = 0.0
                if cohort_left > state[i]:
                    cohort_left = state[i]
                after_lifo[i] = cohort_left
                previous_left = expected_left
            state = after_lifo

        shifted = [0.0 for _ in range(m)]
        for i in range(m - 1):
            shifted[i] = state[i + 1]
        shifted[m - 1] = 0.0
        state = shifted

    effective_carry = 0.0
    denominator = float(m - 1)
    for i in range(m):
        age_fraction = float(m - 1 - i) / denominator
        weight = 1.0 - AGE_LINEAR * age_fraction
        weight = weight + AGE_CURVE * age_fraction * (1.0 - age_fraction)
        if weight < 0.0:
            weight = 0.0
        if weight > 3.0:
            weight = 3.0
        effective_carry = effective_carry + weight * state[i]

    order = S - effective_carry
    if order < 0.0:
        order = 0.0
    if order != order:
        order = 0.0
    if order > 100000.0:
        order = 100000.0
    return float(order)
