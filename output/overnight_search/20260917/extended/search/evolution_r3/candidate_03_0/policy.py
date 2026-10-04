def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    C = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":50.0}
    K = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":5.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":5.0}
    R = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":1.0}
    P = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":2.5}
    H = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":1.0}
    B = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":0.0,"max":1.0}
    G = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}
    J = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":8.0}

    m = len(age)
    if m <= 0:
        return 0.0

    initial = [0.0 for i in range(m)]
    work = [0.0 for i in range(m)]

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        value = float(pipeline[j])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        pipeline_total = pipeline_total + value

    current_plain = P * pipeline_total
    for i in range(m):
        value = float(age[i])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        initial[i] = value
        work[i] = value
        x = (i + 1.0) / m
        weight = R + (1.0 - R) * (x ** A)
        current_plain = current_plain + weight * value

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
                take = G * ((1.0 - B) * expected_take + B * deterministic_take)
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
                take = G * ((1.0 - B) * expected_take + B * deterministic_take)
                if take < 0.0:
                    take = 0.0
                if take > stock:
                    take = stock
                work[i] = stock - take
                before = before + stock

        for i in range(m - 1):
            work[i] = work[i + 1]
        work[m - 1] = 0.0

        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival != arrival or arrival < 0.0:
                arrival = 0.0
            if arrival > 1000000.0:
                arrival = 1000000.0
            work[m - 1] = arrival

    projected_plain = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        weight = R + (1.0 - R) * (x ** A)
        projected_plain = projected_plain + weight * work[i]

    plain_effective = (1.0 - H) * current_plain + H * projected_plain
    seed = K * (S - plain_effective)
    if seed != seed or seed < 0.0:
        seed = 0.0
    if seed > C:
        seed = C

    current_effective = P * pipeline_total
    younger = pipeline_total + seed
    for k in range(m):
        i = m - 1 - k
        x = (i + 1.0) / m
        age_weight = R + (1.0 - R) * (x ** A)
        scale = mu * (i + 1.0) + 1.0
        crowd = younger / scale
        lifo_value = 1.0 / (1.0 + J * crowd)
        service_weight = f + (1.0 - f) * lifo_value
        current_effective = current_effective + age_weight * service_weight * initial[i]
        younger = younger + initial[i]

    projected_effective = 0.0
    younger = seed
    for k in range(m):
        i = m - 1 - k
        x = (i + 1.0) / m
        age_weight = R + (1.0 - R) * (x ** A)
        scale = mu * (i + 1.0) + 1.0
        crowd = younger / scale
        lifo_value = 1.0 / (1.0 + J * crowd)
        service_weight = f + (1.0 - f) * lifo_value
        projected_effective = projected_effective + age_weight * service_weight * work[i]
        younger = younger + work[i]

    effective = (1.0 - H) * current_effective + H * projected_effective
    q = K * (S - effective)

    if q != q or q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return q
