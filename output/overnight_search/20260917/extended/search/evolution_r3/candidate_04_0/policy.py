def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":50.0}
    K = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":5.0}
    GF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    GL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    B = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}
    W0 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W1 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W2 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W3 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    H = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":1.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    J = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":5.0}
    RISK_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":4.0}

    m = len(age)
    if m <= 0:
        return 0.0

    work = [0.0 for i in range(m)]
    pipe = [0.0 for j in range(len(pipeline))]
    weights = [0.0 for i in range(m)]

    for i in range(m):
        value = float(age[i])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        work[i] = value

        if m == 1:
            weight = W3
        else:
            position = 3.0 * i / (m - 1.0)
            if position <= 1.0:
                weight = W0 + (W1 - W0) * position
            elif position <= 2.0:
                weight = W1 + (W2 - W1) * (position - 1.0)
            else:
                weight = W2 + (W3 - W2) * (position - 2.0)
        weights[i] = weight

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        value = float(pipeline[j])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        pipe[j] = value
        pipeline_total = pipeline_total + value

    current_effective = P * pipeline_total
    for i in range(m):
        current_effective = current_effective + weights[i] * work[i]

    fifo_mean = f * mu
    lifo_share = 1.0 - f
    lifo_mean = lifo_share * mu

    fifo_active = fifo_mean > 0.0
    lifo_active = lifo_mean > 0.0

    fifo_w = 0.0
    fifo_r1 = 0.0
    fifo_r2 = 0.0
    if fifo_active:
        fifo_var = f * (mu * cv) * (mu * cv)
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
        lifo_var = lifo_share * (mu * cv) * (mu * cv)
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

    for step in range(L):
        if fifo_active:
            before = 0.0
            for i in range(m):
                stock = work[i]
                expected_take = 0.0
                if stock > 0.0:
                    part1 = fifo_w * (fifo_r1 ** (before + 1.0))
                    part1 = part1 * (1.0 - fifo_r1 ** stock) / (1.0 - fifo_r1)
                    part2 = (1.0 - fifo_w) * (fifo_r2 ** (before + 1.0))
                    part2 = part2 * (1.0 - fifo_r2 ** stock) / (1.0 - fifo_r2)
                    expected_take = part1 + part2

                deterministic_take = fifo_mean - before
                if deterministic_take < 0.0:
                    deterministic_take = 0.0
                if deterministic_take > stock:
                    deterministic_take = stock

                take = GF * ((1.0 - B) * expected_take + B * deterministic_take)
                if take < 0.0:
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
                    part1 = lifo_w * (lifo_r1 ** (before + 1.0))
                    part1 = part1 * (1.0 - lifo_r1 ** stock) / (1.0 - lifo_r1)
                    part2 = (1.0 - lifo_w) * (lifo_r2 ** (before + 1.0))
                    part2 = part2 * (1.0 - lifo_r2 ** stock) / (1.0 - lifo_r2)
                    expected_take = part1 + part2

                deterministic_take = lifo_mean - before
                if deterministic_take < 0.0:
                    deterministic_take = 0.0
                if deterministic_take > stock:
                    deterministic_take = stock

                take = GL * ((1.0 - B) * expected_take + B * deterministic_take)
                if take < 0.0:
                    take = 0.0
                if take > stock:
                    take = stock
                work[i] = stock - take
                before = before + stock

        for i in range(m - 1):
            work[i] = work[i + 1]
        work[m - 1] = 0.0

        if step < len(pipe):
            work[m - 1] = pipe[step]

    projected_effective = 0.0
    for i in range(m):
        projected_effective = projected_effective + weights[i] * work[i]

    base_effective = (1.0 - H) * current_effective + H * projected_effective
    seed = K * (S - base_effective)
    if seed != seed or seed < 0.0:
        seed = 0.0
    if seed > C:
        seed = C

    younger = seed
    crowding_risk = 0.0
    for k in range(m):
        i = m - 1 - k
        stock = work[i]
        denominator = RISK_SCALE * mu * (i + 1.0) + 1.0
        crowd = younger / denominator
        bounded_crowd = crowd / (1.0 + crowd)
        crowding_risk = crowding_risk + stock * bounded_crowd
        younger = younger + stock

    effective = base_effective + H * J * (1.0 - f) * crowding_risk
    q = K * (S - effective)

    if q != q or q < 0.0:
        q = 0.0
    if q > C:
        q = C
    if q > 1000000.0:
        q = 1000000.0
    return q
