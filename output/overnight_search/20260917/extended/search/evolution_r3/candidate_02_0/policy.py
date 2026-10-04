def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":50.0}
    K = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":4.0}
    A = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":4.0}
    R = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}
    H = 0.85 # OPT_PARAM: {"type":"float","initial":0.85,"min":0.0,"max":1.0}
    P = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":2.0}
    B = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}

    m = len(age)
    work = [0.0 for i in range(m)]
    current_effective = 0.0

    for i in range(m):
        x = (i + 1.0) / m
        weight = R + (1.0 - R) * (x ** A)
        value = float(age[i])
        if value < 0.0:
            value = 0.0
        work[i] = value
        current_effective = current_effective + weight * value

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        value = float(pipeline[j])
        if value > 0.0:
            pipeline_total = pipeline_total + value
    current_effective = current_effective + P * pipeline_total

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
        if m > 0:
            work[m - 1] = 0.0

        if step < len(pipeline) and m > 0:
            arrival = float(pipeline[step])
            if arrival > 0.0:
                work[m - 1] = arrival

    projected_effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        weight = R + (1.0 - R) * (x ** A)
        projected_effective = projected_effective + weight * work[i]

    effective = (1.0 - H) * current_effective + H * projected_effective
    q = K * (S - effective)

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return q
