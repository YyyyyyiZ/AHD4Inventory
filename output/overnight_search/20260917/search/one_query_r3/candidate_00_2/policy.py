def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 22.0 # OPT_PARAM: {"type":"float","initial":22.0,"min":0.0,"max":60.0}
    pipeline_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    fifo_capacity_scale = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":2.5}
    lifo_capacity_scale = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":2.5}
    capacity_quantile = -0.4 # OPT_PARAM: {"type":"float","initial":-0.4,"min":-3.0,"max":2.0}
    younger_crowding = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    lifo_spill_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    risk_gain = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}

    m = len(age)
    on_hand = 0.0
    pipeline_stock = 0.0

    for i in range(m):
        x = age[i]
        if x > 0.0:
            on_hand = on_hand + x

    for j in range(len(pipeline)):
        x = pipeline[j]
        if x > 0.0:
            pipeline_stock = pipeline_stock + x

    cumulative_old = 0.0
    deadline_risk = 0.0

    for i in range(m):
        x = age[i]
        if x > 0.0:
            cumulative_old = cumulative_old + x

        horizon = i + 1.0
        fifo_mean = fifo_capacity_scale * f * mu * horizon
        fifo_sd = mu * cv * (f * horizon) ** 0.5
        fifo_capacity = fifo_mean + capacity_quantile * fifo_sd
        if fifo_capacity < 0.0:
            fifo_capacity = 0.0

        lifo_mean = lifo_capacity_scale * (1.0 - f) * mu * horizon
        lifo_sd = mu * cv * ((1.0 - f) * horizon) ** 0.5
        lifo_capacity = lifo_mean + capacity_quantile * lifo_sd
        if lifo_capacity < 0.0:
            lifo_capacity = 0.0

        younger_supply = 0.0
        for k in range(i + 1, m):
            y = age[k]
            if y > 0.0:
                younger_supply = younger_supply + y

        for j in range(len(pipeline)):
            if j + 1 < horizon:
                y = pipeline[j]
                if y > 0.0:
                    younger_supply = younger_supply + y

        lifo_spill = lifo_capacity - younger_crowding * younger_supply
        if lifo_spill < 0.0:
            lifo_spill = 0.0

        accessible_demand = fifo_capacity + lifo_spill_credit * lifo_spill
        excess = cumulative_old - accessible_demand
        if excess > deadline_risk:
            deadline_risk = excess

    q = S - on_hand - pipeline_weight * pipeline_stock
    q = q + risk_gain * deadline_risk

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
