def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":40.0}
    gain = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    old_weight = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":3.0}
    age_shape = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.15,"max":6.0}
    projection_mix = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.0}
    tail_mix = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.0}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        x[i] = float(age[i])

    M_F = f * mu
    M_R = (1.0 - f) * mu

    if M_F > 0.0:
        V_F = f * (mu * cv) * (mu * cv)
        a_F = V_F / (M_F * M_F) - 1.0 / M_F
        root_F = (a_F * a_F - 1.0) ** 0.5
        b_F = 1.0 + a_F + root_F
        c_F = 1.0 + a_F - root_F
        r1_F = 1.0 - 2.0 / (2.0 + M_F * b_F)
        r2_F = 1.0 - 2.0 / (2.0 + M_F * c_F)
        w1_F = 1.0 / b_F
        w2_F = 1.0 / c_F

    if M_R > 0.0:
        g_R = 1.0 - f
        V_R = g_R * (mu * cv) * (mu * cv)
        a_R = V_R / (M_R * M_R) - 1.0 / M_R
        root_R = (a_R * a_R - 1.0) ** 0.5
        b_R = 1.0 + a_R + root_R
        c_R = 1.0 + a_R - root_R
        r1_R = 1.0 - 2.0 / (2.0 + M_R * b_R)
        r2_R = 1.0 - 2.0 / (2.0 + M_R * c_R)
        w1_R = 1.0 / b_R
        w2_R = 1.0 / c_R

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + float(pipeline[t - 1])

        if M_F > 0.0:
            cumulative = 0.0
            previous_expected = 0.0
            for i in range(m):
                v = x[i]
                cumulative = cumulative + v
                n = int(cumulative)
                theta = cumulative - n
                e1 = r1_F * (1.0 - r1_F ** n) / (1.0 - r1_F) + theta * r1_F ** (n + 1)
                e2 = r2_F * (1.0 - r2_F ** n) / (1.0 - r2_F) + theta * r2_F ** (n + 1)
                exact_expected = w1_F * e1 + w2_F * e2
                fluid_expected = min(M_F, cumulative)
                expected = tail_mix * exact_expected + (1.0 - tail_mix) * fluid_expected
                expected = max(0.0, min(cumulative, expected))
                take = expected - previous_expected
                take = max(0.0, min(v, take))
                x[i] = v - take
                previous_expected = expected

        if M_R > 0.0:
            cumulative = 0.0
            previous_expected = 0.0
            for k in range(m):
                i = m - 1 - k
                v = x[i]
                cumulative = cumulative + v
                n = int(cumulative)
                theta = cumulative - n
                e1 = r1_R * (1.0 - r1_R ** n) / (1.0 - r1_R) + theta * r1_R ** (n + 1)
                e2 = r2_R * (1.0 - r2_R ** n) / (1.0 - r2_R) + theta * r2_R ** (n + 1)
                exact_expected = w1_R * e1 + w2_R * e2
                fluid_expected = min(M_R, cumulative)
                expected = tail_mix * exact_expected + (1.0 - tail_mix) * fluid_expected
                expected = max(0.0, min(cumulative, expected))
                take = expected - previous_expected
                take = max(0.0, min(v, take))
                x[i] = v - take
                previous_expected = expected

        shifted = [0.0] * m
        for i in range(1, m):
            shifted[i - 1] = x[i]
        x = shifted

    projected_effective = 0.0
    for i in range(m):
        r = (i + 1.0) / m
        weight = 1.0 + (old_weight - 1.0) * (1.0 - r) ** age_shape
        projected_effective = projected_effective + weight * x[i]

    raw_effective = 0.0
    for i in range(m):
        future_i = i - L
        if future_i >= 0:
            r = (future_i + 1.0) / m
            weight = 1.0 + (old_weight - 1.0) * (1.0 - r) ** age_shape
            raw_effective = raw_effective + weight * float(age[i])

    for j in range(len(pipeline)):
        future_i = m - L + j
        if future_i >= 0 and future_i < m:
            r = (future_i + 1.0) / m
            weight = 1.0 + (old_weight - 1.0) * (1.0 - r) ** age_shape
            raw_effective = raw_effective + weight * float(pipeline[j])

    effective = projection_mix * projected_effective + (1.0 - projection_mix) * raw_effective
    effective = max(0.0, effective)
    q = gain * (S - effective)

    if not (q == q):
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return float(q)
