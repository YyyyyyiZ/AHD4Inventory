def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":45.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    K = 1.1 # OPT_PARAM: {"type":"float","initial":1.1,"min":0.0,"max":5.0}
    K2 = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":4.0}
    GF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    GL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    B = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.0}
    W0 = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.0,"max":4.0}
    W1 = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":4.0}
    W2 = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":4.0}
    W3 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W4 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    CUR = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    QUIET = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":-1.0,"max":2.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    J = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":6.0}
    RISK_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":5.0}

    m = len(age)
    if m <= 0:
        return 0.0

    work = [0.0 for i in range(m)]
    quiet = [0.0 for i in range(m)]
    pipe = [0.0 for j in range(len(pipeline))]
    weights = [0.0 for i in range(m)]

    current_effective = 0.0
    pipeline_total = 0.0

    for i in range(m):
        value = float(age[i])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        work[i] = value
        quiet[i] = value

        if m == 1:
            weight = W4
        else:
            position = 4.0 * i / (m - 1.0)
            if position <= 1.0:
                weight = W0 + (W1 - W0) * position
            elif position <= 2.0:
                weight = W1 + (W2 - W1) * (position - 1.0)
            elif position <= 3.0:
                weight = W2 + (W3 - W2) * (position - 2.0)
            else:
                weight = W3 + (W4 - W3) * (position - 3.0)
        weights[i] = weight
        current_effective = current_effective + weight * value

    for j in range(len(pipeline)):
        value = float(pipeline[j])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        pipe[j] = value
        pipeline_total = pipeline_total + value

    current_effective = current_effective + P * pipeline_total

    f_use = float(f)
    if f_use != f_use:
        f_use = 0.0
    if f_use < 0.0:
        f_use = 0.0
    if f_use > 1.0:
        f_use = 1.0

    demand_mean = float(mu)
    demand_cv = float(cv)
    if demand_mean != demand_mean or demand_mean < 0.0:
        demand_mean = 0.0
    if demand_cv != demand_cv or demand_cv < 0.0:
        demand_cv = 0.0

    fifo_mean = f_use * demand_mean
    lifo_share = 1.0 - f_use
    lifo_mean = lifo_share * demand_mean
    variance_scale = (demand_mean * demand_cv) * (demand_mean * demand_cv)

    fifo_active = fifo_mean > 0.0
    lifo_active = lifo_mean > 0.0

    fifo_w = 0.0
    fifo_r1 = 0.0
    fifo_r2 = 0.0
    if fifo_active:
        fifo_var = f_use * variance_scale
        fifo_a = fifo_var / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        if fifo_a < 1.0:
            fifo_a = 1.0
        fifo_root = (fifo_a * fifo_a - 1.0) ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_w = 1.0 / fifo_b
        fifo_p1 = 2.0 / (2.0 + fifo_mean * fifo_b)
        fifo_p2 = 2.0 / (2.0 + fifo_mean * fifo_c)
        fifo_r1 = 1.0 - fifo_p1
        fifo_r2 = 1.0 - fifo_p2

    lifo_w = 0.0
    lifo_r1 = 0.0
    lifo_r2 = 0.0
    if lifo_active:
        lifo_var = lifo_share * variance_scale
        lifo_a = lifo_var / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        if lifo_a < 1.0:
            lifo_a = 1.0
        lifo_root = (lifo_a * lifo_a - 1.0) ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_w = 1.0 / lifo_b
        lifo_p1 = 2.0 / (2.0 + lifo_mean * lifo_b)
        lifo_p2 = 2.0 / (2.0 + lifo_mean * lifo_c)
        lifo_r1 = 1.0 - lifo_p1
        lifo_r2 = 1.0 - lifo_p2

    steps = int(L)
    if steps < 0:
        steps = 0
    if steps > 20:
        steps = 20

    for step in range(steps):
        if fifo_active:
            before = 0.0
            for i in range(m):
                stock = work[i]
                expected_take = 0.0
                if stock > 0.0:
                    denominator1 = 1.0 - fifo_r1
                    denominator2 = 1.0 - fifo_r2
                    if denominator1 > 0.000000000001:
                        part1 = fifo_w * (fifo_r1 ** (before + 1.0))
                        part1 = part1 * (1.0 - fifo_r1 ** stock) / denominator1
                    else:
                        part1 = fifo_w * stock
                    if denominator2 > 0.000000000001:
                        part2 = (1.0 - fifo_w) * (fifo_r2 ** (before + 1.0))
                        part2 = part2 * (1.0 - fifo_r2 ** stock) / denominator2
                    else:
                        part2 = (1.0 - fifo_w) * stock
                    expected_take = part1 + part2

                deterministic_take = fifo_mean - before
                if deterministic_take < 0.0:
                    deterministic_take = 0.0
                if deterministic_take > stock:
                    deterministic_take = stock

                take = GF * ((1.0 - B) * expected_take + B * deterministic_take)
                if take != take or take < 0.0:
                    take = 0.0
                if take > stock:
                    take = stock
                work[i] = stock - take
                before = before + stock

        if lifo_active:
            before = 0.0
            for k in range(m):
                i = m - 1 - k
                stock = work[i]
                expected_take = 0.0
                if stock > 0.0:
                    denominator1 = 1.0 - lifo_r1
                    denominator2 = 1.0 - lifo_r2
                    if denominator1 > 0.000000000001:
                        part1 = lifo_w * (lifo_r1 ** (before + 1.0))
                        part1 = part1 * (1.0 - lifo_r1 ** stock) / denominator1
                    else:
                        part1 = lifo_w * stock
                    if denominator2 > 0.000000000001:
                        part2 = (1.0 - lifo_w) * (lifo_r2 ** (before + 1.0))
                        part2 = part2 * (1.0 - lifo_r2 ** stock) / denominator2
                    else:
                        part2 = (1.0 - lifo_w) * stock
                    expected_take = part1 + part2

                deterministic_take = lifo_mean - before
                if deterministic_take < 0.0:
                    deterministic_take = 0.0
                if deterministic_take > stock:
                    deterministic_take = stock

                take = GL * ((1.0 - B) * expected_take + B * deterministic_take)
                if take != take or take < 0.0:
                    take = 0.0
                if take > stock:
                    take = stock
                work[i] = stock - take
                before = before + stock

        for i in range(m - 1):
            work[i] = work[i + 1]
            quiet[i] = quiet[i + 1]
        work[m - 1] = 0.0
        quiet[m - 1] = 0.0

        if step < len(pipe):
            work[m - 1] = pipe[step]
            quiet[m - 1] = pipe[step]

    expected_effective = 0.0
    quiet_effective = 0.0
    for i in range(m):
        expected_effective = expected_effective + weights[i] * work[i]
        quiet_effective = quiet_effective + weights[i] * quiet[i]

    base_effective = expected_effective
    base_effective = base_effective + CUR * (current_effective - expected_effective)
    base_effective = base_effective + QUIET * (quiet_effective - expected_effective)

    gap = S - base_effective
    seed = 0.0
    if gap > 0.0:
        seed = K * gap + K2 * gap * gap / (demand_mean + gap + 1.0)
    if seed != seed or seed < 0.0:
        seed = 0.0
    if seed > C:
        seed = C

    younger = seed
    crowding_risk = 0.0
    for k in range(m):
        i = m - 1 - k
        stock = work[i]
        lifetime = i + 1.0
        denominator = RISK_SCALE * demand_mean * lifetime + 1.0
        crowd = younger / denominator
        bounded_crowd = crowd / (1.0 + crowd)
        urgency = (m - i) / m
        crowding_risk = crowding_risk + stock * bounded_crowd * urgency
        younger = younger + stock

    effective = base_effective + J * (1.0 - f_use) * crowding_risk
    gap = S - effective

    q = 0.0
    if gap > 0.0:
        q = K * gap + K2 * gap * gap / (demand_mean + gap + 1.0)

    if q != q or q < 0.0:
        q = 0.0
    if q > C:
        q = C
    if q > 1000000.0:
        q = 1000000.0
    return q
