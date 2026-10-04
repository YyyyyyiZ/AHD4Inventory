def compute_order_amount(age, pipeline, mu, cv, f, L):
    BASE = 4.0 # OPT_PARAM: {"type":"float","initial":4.0,"min":0.0,"max":12.0}
    TARGET = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    UP_GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    DOWN_GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    AGE_BIAS = -0.5 # OPT_PARAM: {"type":"float","initial":-0.5,"min":-1.5,"max":2.0}
    AGE_POWER = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":6.0}
    PROJECTION = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.0}
    SMOOTHING = 0.4 # OPT_PARAM: {"type":"float","initial":0.4,"min":0.0,"max":2.0}
    MAX_ORDER = 25.0 # OPT_PARAM: {"type":"float","initial":25.0,"min":0.0,"max":60.0}

    m = len(age)
    state = [0.0] * m
    for i in range(m):
        state[i] = max(0.0, float(age[i]))

    mf = f * mu
    vf = f * (mu * cv) * (mu * cv)
    wf = 0.0
    pf1 = 1.0
    pf2 = 1.0
    rf1 = 0.0
    rf2 = 0.0
    if mf > 0.0:
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

    gl = 1.0 - f
    ml = gl * mu
    vl = gl * (mu * cv) * (mu * cv)
    wl = 0.0
    pl1 = 1.0
    pl2 = 1.0
    rl1 = 0.0
    rl2 = 0.0
    if ml > 0.0:
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

    for t in range(L):
        if mf > 0.0:
            transformed = [0.0] * m
            cumulative = 0.0
            previous_left = 0.0
            for i in range(m):
                cumulative = cumulative + state[i]
                trunc1 = rf1 * (1.0 - rf1 ** cumulative) / pf1
                trunc2 = rf2 * (1.0 - rf2 ** cumulative) / pf2
                left = cumulative - wf * trunc1 - (1.0 - wf) * trunc2
                bucket_left = left - previous_left
                if bucket_left < 0.0:
                    bucket_left = 0.0
                if bucket_left > state[i]:
                    bucket_left = state[i]
                transformed[i] = state[i] + PROJECTION * (bucket_left - state[i])
                previous_left = left
            state = transformed

        if ml > 0.0:
            transformed = [0.0] * m
            cumulative = 0.0
            previous_left = 0.0
            for k in range(m):
                i = m - 1 - k
                cumulative = cumulative + state[i]
                trunc1 = rl1 * (1.0 - rl1 ** cumulative) / pl1
                trunc2 = rl2 * (1.0 - rl2 ** cumulative) / pl2
                left = cumulative - wl * trunc1 - (1.0 - wl) * trunc2
                bucket_left = left - previous_left
                if bucket_left < 0.0:
                    bucket_left = 0.0
                if bucket_left > state[i]:
                    bucket_left = state[i]
                transformed[i] = state[i] + PROJECTION * (bucket_left - state[i])
                previous_left = left
            state = transformed

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = state[i + 1]
        if t < len(pipeline):
            shifted[m - 1] = max(0.0, float(pipeline[t]))
        else:
            shifted[m - 1] = 0.0
        state = shifted

    projected_stock = 0.0
    age_risk = 0.0
    for i in range(m):
        projected_stock = projected_stock + state[i]
        remaining_fraction = (i + 1.0) / m
        age_risk = age_risk + state[i] * ((1.0 - remaining_fraction) ** AGE_POWER)

    effective_stock = projected_stock + AGE_BIAS * age_risk
    gap = TARGET - effective_stock
    if gap >= 0.0:
        raw = BASE + UP_GAIN * gap
    else:
        raw = BASE + DOWN_GAIN * gap

    recent_order = BASE
    if len(pipeline) > 0:
        recent_order = 0.0
        for j in range(len(pipeline)):
            recent_order = recent_order + float(pipeline[j])
        recent_order = recent_order / len(pipeline)
    raw = raw + SMOOTHING * (recent_order - BASE)

    if raw != raw:
        raw = 0.0
    if raw < 0.0:
        raw = 0.0
    if raw > MAX_ORDER:
        raw = MAX_ORDER
    return float(raw)
