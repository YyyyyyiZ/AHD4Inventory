def compute_order_amount(age, pipeline, mu, cv, f, L):
    arrival_target = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":60.0}
    fifo_demand_scale = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.0,"max":2.5}
    lifo_demand_scale = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.0,"max":2.5}
    survivor_floor = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.2}
    survivor_power = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.15,"max":5.0}

    m = len(age)
    work = [0.0] * m

    for i in range(m):
        x = age[i]
        if x < 0.0:
            x = 0.0
        work[i] = x

    for t in range(L):
        fifo_demand = fifo_demand_scale * f * mu
        if fifo_demand < 0.0:
            fifo_demand = 0.0

        for i in range(m):
            available = work[i]
            take = available
            if take > fifo_demand:
                take = fifo_demand
            work[i] = available - take
            fifo_demand = fifo_demand - take

        lifo_demand = lifo_demand_scale * (1.0 - f) * mu
        if lifo_demand < 0.0:
            lifo_demand = 0.0

        for k in range(m):
            i = m - 1 - k
            available = work[i]
            take = available
            if take > lifo_demand:
                take = lifo_demand
            work[i] = available - take
            lifo_demand = lifo_demand - take

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = work[i + 1]

        arrival = 0.0
        if t < len(pipeline):
            arrival = pipeline[t]
            if arrival < 0.0:
                arrival = 0.0
        shifted[m - 1] = arrival
        work = shifted

    survivor_credit = 0.0
    for i in range(m):
        relative_life = (i + 1.0) / m
        weight = survivor_floor + (1.0 - survivor_floor) * relative_life ** survivor_power
        survivor_credit = survivor_credit + work[i] * weight

    q = arrival_target - survivor_credit

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
