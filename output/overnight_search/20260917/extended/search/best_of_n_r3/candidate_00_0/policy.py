def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":60.0}
    age_power = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":4.0}
    projection_mix = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":1.0}
    pipeline_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.8}

    m = len(age)
    work = [0.0] * m
    updated = [0.0] * m
    effective_now = 0.0

    for i in range(m):
        value = max(0.0, float(age[i]))
        work[i] = value
        relative_life = (i + 1.0) / m
        effective_now = effective_now + value * (relative_life ** age_power)

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + max(0.0, float(pipeline[j]))
    effective_now = effective_now + pipeline_weight * pipeline_total

    fifo_group = max(0.0, min(1.0, float(f)))
    lifo_group = 1.0 - fifo_group

    fifo_active = fifo_group > 0.0
    lifo_active = lifo_group > 0.0

    if fifo_active:
        fifo_mean = fifo_group * mu
        fifo_variance = fifo_group * (mu * cv) * (mu * cv)
        fifo_a = fifo_variance / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        fifo_root = max(0.0, fifo_a * fifo_a - 1.0) ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_weight = 1.0 / fifo_b
        fifo_r1 = 1.0 - 2.0 / (2.0 + fifo_mean * fifo_b)
        fifo_r2 = 1.0 - 2.0 / (2.0 + fifo_mean * fifo_c)

    if lifo_active:
        lifo_mean = lifo_group * mu
        lifo_variance = lifo_group * (mu * cv) * (mu * cv)
        lifo_a = lifo_variance / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        lifo_root = max(0.0, lifo_a * lifo_a - 1.0) ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_weight = 1.0 / lifo_b
        lifo_r1 = 1.0 - 2.0 / (2.0 + lifo_mean * lifo_b)
        lifo_r2 = 1.0 - 2.0 / (2.0 + lifo_mean * lifo_c)

    for t in range(L):
        if fifo_active:
            cumulative = 0.0
            for i in range(m):
                quantity = work[i]
                upper = cumulative + quantity
                upper_scaled = upper / demand_scale
                lower_scaled = cumulative / demand_scale
                upper_min = demand_scale * (
                    fifo_weight * fifo_r1 * (1.0 - fifo_r1 ** upper_scaled) / (1.0 - fifo_r1)
                    + (1.0 - fifo_weight) * fifo_r2 * (1.0 - fifo_r2 ** upper_scaled) / (1.0 - fifo_r2)
                )
                lower_min = demand_scale * (
                    fifo_weight * fifo_r1 * (1.0 - fifo_r1 ** lower_scaled) / (1.0 - fifo_r1)
                    + (1.0 - fifo_weight) * fifo_r2 * (1.0 - fifo_r2 ** lower_scaled) / (1.0 - fifo_r2)
                )
                consumed = max(0.0, min(quantity, upper_min - lower_min))
                updated[i] = quantity - consumed
                cumulative = upper
            for i in range(m):
                work[i] = updated[i]

        if lifo_active:
            cumulative = 0.0
            for k in range(m):
                i = m - 1 - k
                quantity = work[i]
                upper = cumulative + quantity
                upper_scaled = upper / demand_scale
                lower_scaled = cumulative / demand_scale
                upper_min = demand_scale * (
                    lifo_weight * lifo_r1 * (1.0 - lifo_r1 ** upper_scaled) / (1.0 - lifo_r1)
                    + (1.0 - lifo_weight) * lifo_r2 * (1.0 - lifo_r2 ** upper_scaled) / (1.0 - lifo_r2)
                )
                lower_min = demand_scale * (
                    lifo_weight * lifo_r1 * (1.0 - lifo_r1 ** lower_scaled) / (1.0 - lifo_r1)
                    + (1.0 - lifo_weight) * lifo_r2 * (1.0 - lifo_r2 ** lower_scaled) / (1.0 - lifo_r2)
                )
                consumed = max(0.0, min(quantity, upper_min - lower_min))
                updated[i] = quantity - consumed
                cumulative = upper
            for i in range(m):
                work[i] = updated[i]

        for i in range(m - 1):
            work[i] = work[i + 1]
        work[m - 1] = 0.0
        if t < len(pipeline):
            work[m - 1] = max(0.0, float(pipeline[t]))

    effective_future = 0.0
    for i in range(m):
        relative_life = (i + 1.0) / m
        effective_future = effective_future + work[i] * (relative_life ** age_power)

    effective = projection_mix * effective_future + (1.0 - projection_mix) * effective_now
    order = S - effective
    return max(0.0, min(C, order))
