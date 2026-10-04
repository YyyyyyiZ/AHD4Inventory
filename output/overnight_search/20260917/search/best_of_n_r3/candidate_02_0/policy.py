def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.2}
    feedback = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    position_blend = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}
    terminal_weight = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.3,"max":1.8}
    lead_credit = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.5}

    m = len(age)
    muv = float(mu)
    cvv = float(cv)
    fv = float(f)

    position = 0.0
    x = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value < 0.0:
            value = 0.0
        x[i] = value
        position = position + value

    for j in range(len(pipeline)):
        value = float(pipeline[j])
        if value > 0.0:
            position = position + value

    groups = [fv, 1.0 - fv]
    active = [False, False]
    r1 = [0.0, 0.0]
    r2 = [0.0, 0.0]
    mix1 = [0.0, 0.0]

    for s in range(2):
        g = groups[s]
        if g > 0.0 and muv > 0.0:
            mean_stream = g * muv
            variance_stream = g * (muv * cvv) * (muv * cvv)
            a = variance_stream / (mean_stream * mean_stream) - 1.0 / mean_stream
            root_arg = a * a - 1.0
            if root_arg < 0.0:
                root_arg = 0.0
            root = root_arg ** 0.5
            b = 1.0 + a + root
            c = 1.0 + a - root
            p1 = 2.0 / (2.0 + mean_stream * b)
            p2 = 2.0 / (2.0 + mean_stream * c)
            r1[s] = 1.0 - p1
            r2[s] = 1.0 - p2
            mix1[s] = 1.0 / b
            active[s] = True

    for t in range(int(L)):
        if t > 0 and t - 1 < len(pipeline):
            arrival = float(pipeline[t - 1])
            if arrival > 0.0:
                x[m - 1] = x[m - 1] + arrival

        cumulative = 0.0
        for i in range(m):
            block = x[i]
            consumed = 0.0
            if block > 0.0 and active[0]:
                ra = r1[0]
                rb = r2[0]
                wa = mix1[0]
                part_a = wa * (ra ** (cumulative + 1.0)) * (1.0 - ra ** block) / (1.0 - ra)
                part_b = (1.0 - wa) * (rb ** (cumulative + 1.0)) * (1.0 - rb ** block) / (1.0 - rb)
                consumed = demand_scale * (part_a + part_b)
                if consumed > block:
                    consumed = block
                if consumed < 0.0:
                    consumed = 0.0
            x[i] = block - consumed
            cumulative = cumulative + block

        cumulative = 0.0
        for z in range(m):
            i = m - 1 - z
            block = x[i]
            consumed = 0.0
            if block > 0.0 and active[1]:
                ra = r1[1]
                rb = r2[1]
                wa = mix1[1]
                part_a = wa * (ra ** (cumulative + 1.0)) * (1.0 - ra ** block) / (1.0 - ra)
                part_b = (1.0 - wa) * (rb ** (cumulative + 1.0)) * (1.0 - rb ** block) / (1.0 - rb)
                consumed = demand_scale * (part_a + part_b)
                if consumed > block:
                    consumed = block
                if consumed < 0.0:
                    consumed = 0.0
            x[i] = block - consumed
            cumulative = cumulative + block

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = x[i + 1]
        shifted[m - 1] = 0.0
        x = shifted

    projected_effective = 0.0
    denominator = float(max(1, m - 1))
    for i in range(m):
        freshness = float(i) / denominator
        weight = terminal_weight + (1.0 - terminal_weight) * freshness
        projected_effective = projected_effective + weight * x[i]

    horizon = float(m + int(L))
    median_adjustment = 1.0 - (cvv * cvv) / (9.0 * horizon)
    if median_adjustment < 0.05:
        median_adjustment = 0.05
    cap_proxy = horizon * muv * median_adjustment * median_adjustment * median_adjustment

    state_measure = position_blend * position + (1.0 - position_blend) * projected_effective
    target = S * cap_proxy - (1.0 - position_blend) * lead_credit * muv * float(L)
    order = target - feedback * state_measure

    if order != order:
        order = 0.0
    if order < 0.0:
        order = 0.0
    if order > 1000000.0:
        order = 1000000.0
    return float(order)
