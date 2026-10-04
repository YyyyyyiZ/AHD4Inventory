def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 22.0 # OPT_PARAM: {"type":"float","initial":22.0,"min":0.0,"max":60.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":1.8}
    stock_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    old_weight_1 = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}
    old_weight_2 = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}
    congestion_weight = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-1.5,"max":1.5}

    m = len(age)
    pipe_len = len(pipeline)
    state = [0.0] * m

    for i in range(m):
        value = float(age[i])
        if value < 0.0 or value != value:
            value = 0.0
        state[i] = value

    base_variance = (mu * cv) * (mu * cv)

    fifo_mean = f * mu
    fifo_variance = f * base_variance
    fifo_w1 = 0.0
    fifo_p1 = 1.0
    fifo_p2 = 1.0
    fifo_r1 = 0.0
    fifo_r2 = 0.0

    if fifo_mean > 0.0:
        fifo_a = fifo_variance / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        if fifo_a < 1.0:
            fifo_a = 1.0
        fifo_root = (fifo_a * fifo_a - 1.0) ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_w1 = 1.0 / fifo_b
        fifo_p1 = 2.0 / (2.0 + fifo_mean * fifo_b)
        fifo_p2 = 2.0 / (2.0 + fifo_mean * fifo_c)
        fifo_r1 = 1.0 - fifo_p1
        fifo_r2 = 1.0 - fifo_p2

    lifo_share = 1.0 - f
    lifo_mean = lifo_share * mu
    lifo_variance = lifo_share * base_variance
    lifo_w1 = 0.0
    lifo_p1 = 1.0
    lifo_p2 = 1.0
    lifo_r1 = 0.0
    lifo_r2 = 0.0

    if lifo_mean > 0.0:
        lifo_a = lifo_variance / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        if lifo_a < 1.0:
            lifo_a = 1.0
        lifo_root = (lifo_a * lifo_a - 1.0) ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_w1 = 1.0 / lifo_b
        lifo_p1 = 2.0 / (2.0 + lifo_mean * lifo_b)
        lifo_p2 = 2.0 / (2.0 + lifo_mean * lifo_c)
        lifo_r1 = 1.0 - lifo_p1
        lifo_r2 = 1.0 - lifo_p2

    for lead_step in range(L):
        if fifo_mean > 0.0:
            cumulative = 0.0
            for i in range(m):
                available = state[i]
                upper = cumulative + available

                fifo_upper_1 = fifo_r1 * (1.0 - fifo_r1 ** upper) / fifo_p1
                fifo_upper_2 = fifo_r2 * (1.0 - fifo_r2 ** upper) / fifo_p2
                fifo_lower_1 = fifo_r1 * (1.0 - fifo_r1 ** cumulative) / fifo_p1
                fifo_lower_2 = fifo_r2 * (1.0 - fifo_r2 ** cumulative) / fifo_p2

                truncated_upper = fifo_w1 * fifo_upper_1 + (1.0 - fifo_w1) * fifo_upper_2
                truncated_lower = fifo_w1 * fifo_lower_1 + (1.0 - fifo_w1) * fifo_lower_2
                depletion = demand_scale * (truncated_upper - truncated_lower)

                if depletion < 0.0:
                    depletion = 0.0
                if depletion > available:
                    depletion = available

                state[i] = available - depletion
                cumulative = upper

        if lifo_mean > 0.0:
            cumulative = 0.0
            for reverse_i in range(m):
                i = m - 1 - reverse_i
                available = state[i]
                upper = cumulative + available

                lifo_upper_1 = lifo_r1 * (1.0 - lifo_r1 ** upper) / lifo_p1
                lifo_upper_2 = lifo_r2 * (1.0 - lifo_r2 ** upper) / lifo_p2
                lifo_lower_1 = lifo_r1 * (1.0 - lifo_r1 ** cumulative) / lifo_p1
                lifo_lower_2 = lifo_r2 * (1.0 - lifo_r2 ** cumulative) / lifo_p2

                truncated_upper = lifo_w1 * lifo_upper_1 + (1.0 - lifo_w1) * lifo_upper_2
                truncated_lower = lifo_w1 * lifo_lower_1 + (1.0 - lifo_w1) * lifo_lower_2
                depletion = demand_scale * (truncated_upper - truncated_lower)

                if depletion < 0.0:
                    depletion = 0.0
                if depletion > available:
                    depletion = available

                state[i] = available - depletion
                cumulative = upper

        for i in range(m - 1):
            state[i] = state[i + 1]

        incoming = 0.0
        if lead_step < pipe_len:
            incoming = float(pipeline[lead_step])
            if incoming < 0.0 or incoming != incoming:
                incoming = 0.0
        state[m - 1] = incoming

    projected_stock = 0.0
    projected_old_1 = 0.0
    projected_old_2 = 0.0

    for i in range(m):
        quantity = state[i]
        remaining_fraction = float(i + 1) / float(m)
        oldness = 1.0 - remaining_fraction
        projected_stock = projected_stock + quantity
        projected_old_1 = projected_old_1 + oldness * quantity
        projected_old_2 = projected_old_2 + oldness * oldness * quantity

    denominator = S + 1.0
    raw_order = S
    raw_order = raw_order - stock_weight * projected_stock
    raw_order = raw_order - old_weight_1 * projected_old_1
    raw_order = raw_order - old_weight_2 * projected_old_2
    raw_order = raw_order - congestion_weight * projected_stock * projected_stock / denominator

    if raw_order != raw_order or raw_order < 0.0:
        raw_order = 0.0
    if raw_order > 1000.0:
        raw_order = 1000.0

    return float(raw_order)
