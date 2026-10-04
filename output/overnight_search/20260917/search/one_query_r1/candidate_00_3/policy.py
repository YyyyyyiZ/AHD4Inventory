def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 19.0 # OPT_PARAM: {"type":"float","initial":19.0,"min":0.0,"max":60.0}
    WP = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":1.5}
    B = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":3.0}
    SPILL = 0.70 # OPT_PARAM: {"type":"float","initial":0.70,"min":0.0,"max":1.0}
    H = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.2,"max":3.0}
    PD = 0.50 # OPT_PARAM: {"type":"float","initial":0.50,"min":0.0,"max":2.0}

    fifo_zero = 1.0
    if f > 0.0:
        fifo_mean = f * mu
        fifo_variance = f * (mu * cv) * (mu * cv)
        fifo_a = fifo_variance / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        fifo_root = max(0.0, fifo_a * fifo_a - 1.0) ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_weight = 1.0 / fifo_b
        fifo_p1 = 2.0 / (2.0 + fifo_mean * fifo_b)
        fifo_p2 = 2.0 / (2.0 + fifo_mean * fifo_c)
        fifo_zero = fifo_weight * fifo_p1 + (1.0 - fifo_weight) * fifo_p2

    lifo_share = 1.0 - f
    lifo_zero = 1.0
    if lifo_share > 0.0:
        lifo_mean = lifo_share * mu
        lifo_variance = lifo_share * (mu * cv) * (mu * cv)
        lifo_a = lifo_variance / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        lifo_root = max(0.0, lifo_a * lifo_a - 1.0) ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_weight = 1.0 / lifo_b
        lifo_p1 = 2.0 / (2.0 + lifo_mean * lifo_b)
        lifo_p2 = 2.0 / (2.0 + lifo_mean * lifo_c)
        lifo_zero = lifo_weight * lifo_p1 + (1.0 - lifo_weight) * lifo_p2

    total_zero = fifo_zero * lifo_zero
    m = len(age)
    denominator = float(max(1, m - 1))
    age_total = 0.0
    doomed_stock = 0.0

    for i in range(m):
        stock = float(age[i])
        age_total = age_total + stock
        position = float(i) / denominator
        priority_zero = (1.0 - position) * fifo_zero + position * lifo_zero
        no_service_base = SPILL * priority_zero + (1.0 - SPILL) * total_zero
        if no_service_base < 0.0:
            no_service_base = 0.0
        if no_service_base > 1.0:
            no_service_base = 1.0
        remaining_life = float(i + 1)
        doom_probability = no_service_base ** (H * remaining_life)
        doomed_stock = doomed_stock + stock * doom_probability

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + float(pipeline[j])

    pipeline_doom_probability = total_zero ** (H * float(m))
    pipeline_doom = PD * pipeline_total * pipeline_doom_probability
    inventory_position = age_total + WP * pipeline_total
    q = S - inventory_position + B * (doomed_stock + pipeline_doom)

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 120.0:
        q = 120.0
    return float(q)
