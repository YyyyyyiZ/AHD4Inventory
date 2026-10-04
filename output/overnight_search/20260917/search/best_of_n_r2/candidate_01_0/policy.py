def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    mean_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    mean_age_credit = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":3.0}
    tail_credit = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":-1.0,"max":2.5}
    tail_age_credit = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":3.0}
    crowding_credit = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":2.0}

    m = len(age)
    state = [0.0] * m
    quiet = [0.0] * m

    for i in range(m):
        x = float(age[i])
        if x < 0.0:
            x = 0.0
        state[i] = x
        quiet[i] = x

    mean_fifo = f * mu
    var_fifo = f * (mu * cv) * (mu * cv)
    fifo_active = mean_fifo > 0.0

    fifo_w1 = 0.0
    fifo_p1 = 1.0
    fifo_r1 = 0.0
    fifo_w2 = 0.0
    fifo_p2 = 1.0
    fifo_r2 = 0.0

    if fifo_active:
        fifo_a = var_fifo / (mean_fifo * mean_fifo) - 1.0 / mean_fifo
        if fifo_a < 1.0:
            fifo_a = 1.0
        fifo_root = (fifo_a * fifo_a - 1.0) ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_w1 = 1.0 / fifo_b
        fifo_w2 = 1.0 - fifo_w1
        fifo_p1 = 2.0 / (2.0 + mean_fifo * fifo_b)
        fifo_p2 = 2.0 / (2.0 + mean_fifo * fifo_c)
        fifo_r1 = 1.0 - fifo_p1
        fifo_r2 = 1.0 - fifo_p2

    lifo_share = 1.0 - f
    mean_lifo = lifo_share * mu
    var_lifo = lifo_share * (mu * cv) * (mu * cv)
    lifo_active = mean_lifo > 0.0

    lifo_w1 = 0.0
    lifo_p1 = 1.0
    lifo_r1 = 0.0
    lifo_w2 = 0.0
    lifo_p2 = 1.0
    lifo_r2 = 0.0

    if lifo_active:
        lifo_a = var_lifo / (mean_lifo * mean_lifo) - 1.0 / mean_lifo
        if lifo_a < 1.0:
            lifo_a = 1.0
        lifo_root = (lifo_a * lifo_a - 1.0) ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_w1 = 1.0 / lifo_b
        lifo_w2 = 1.0 - lifo_w1
        lifo_p1 = 2.0 / (2.0 + mean_lifo * lifo_b)
        lifo_p2 = 2.0 / (2.0 + mean_lifo * lifo_c)
        lifo_r1 = 1.0 - lifo_p1
        lifo_r2 = 1.0 - lifo_p2

    for step in range(L):
        after_fifo = [0.0] * m

        if fifo_active:
            cumulative = 0.0
            previous_remainder = 0.0
            for i in range(m):
                cumulative = cumulative + state[i]
                fifo_min1 = fifo_r1 * (1.0 - fifo_r1 ** cumulative) / fifo_p1
                fifo_min2 = fifo_r2 * (1.0 - fifo_r2 ** cumulative) / fifo_p2
                expected_minimum = fifo_w1 * fifo_min1 + fifo_w2 * fifo_min2
                cumulative_remainder = cumulative - expected_minimum
                value = cumulative_remainder - previous_remainder
                if value < 0.0:
                    value = 0.0
                if value > state[i]:
                    value = state[i]
                after_fifo[i] = value
                previous_remainder = cumulative_remainder
        else:
            for i in range(m):
                after_fifo[i] = state[i]

        after_both = [0.0] * m

        if lifo_active:
            cumulative = 0.0
            previous_remainder = 0.0
            for k in range(m):
                i = m - 1 - k
                cumulative = cumulative + after_fifo[i]
                lifo_min1 = lifo_r1 * (1.0 - lifo_r1 ** cumulative) / lifo_p1
                lifo_min2 = lifo_r2 * (1.0 - lifo_r2 ** cumulative) / lifo_p2
                expected_minimum = lifo_w1 * lifo_min1 + lifo_w2 * lifo_min2
                cumulative_remainder = cumulative - expected_minimum
                value = cumulative_remainder - previous_remainder
                if value < 0.0:
                    value = 0.0
                if value > after_fifo[i]:
                    value = after_fifo[i]
                after_both[i] = value
                previous_remainder = cumulative_remainder
        else:
            for i in range(m):
                after_both[i] = after_fifo[i]

        next_state = [0.0] * m
        next_quiet = [0.0] * m

        for i in range(m - 1):
            next_state[i] = after_both[i + 1]
            next_quiet[i] = quiet[i + 1]

        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival < 0.0:
                arrival = 0.0
            next_state[m - 1] = next_state[m - 1] + arrival
            next_quiet[m - 1] = next_quiet[m - 1] + arrival

        state = next_state
        quiet = next_quiet

    expected_total = 0.0
    expected_oldness = 0.0
    tail_total = 0.0
    tail_oldness = 0.0

    age_denominator = float(m - 1)
    if age_denominator < 1.0:
        age_denominator = 1.0

    for i in range(m):
        oldness = float(m - 1 - i) / age_denominator
        expected_total = expected_total + state[i]
        expected_oldness = expected_oldness + oldness * state[i]

        tail = quiet[i] - state[i]
        if tail < 0.0:
            tail = 0.0
        tail_total = tail_total + tail
        tail_oldness = tail_oldness + oldness * tail

    scale = mu * float(m) + 1.0
    crowding = expected_total * tail_total / scale

    q = S
    q = q - mean_credit * expected_total
    q = q - mean_age_credit * expected_oldness
    q = q - tail_credit * tail_total
    q = q - tail_age_credit * tail_oldness
    q = q - crowding_credit * crowding

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 120.0:
        q = 120.0

    return float(q)
