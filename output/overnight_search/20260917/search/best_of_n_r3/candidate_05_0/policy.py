def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    BLEND = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":1.0}
    GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":2.5}
    D_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":2.0}
    W_OLD = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.5}
    W_NEW = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.5}
    W_SHAPE = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.2,"max":5.0}

    m = len(age)
    lead = int(L)
    if m <= 0:
        return 0.0
    if lead < 0:
        lead = 0

    demand_scale = float(D_SCALE)
    mean_total = float(mu)
    sigma_total = mean_total * float(cv)
    fifo_fraction = float(f)
    lifo_fraction = 1.0 - fifo_fraction

    fifo_mean = fifo_fraction * mean_total
    fifo_var = fifo_fraction * sigma_total * sigma_total
    fifo_active = fifo_mean > 0.0
    fifo_weight = 0.0
    fifo_p1 = 1.0
    fifo_p2 = 1.0
    fifo_r1 = 0.0
    fifo_r2 = 0.0
    if fifo_active:
        fifo_a = fifo_var / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        fifo_disc = fifo_a * fifo_a - 1.0
        if fifo_disc < 0.0:
            fifo_disc = 0.0
        fifo_root = fifo_disc ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_weight = 1.0 / fifo_b
        fifo_p1 = 2.0 / (2.0 + fifo_mean * fifo_b)
        fifo_p2 = 2.0 / (2.0 + fifo_mean * fifo_c)
        fifo_r1 = 1.0 - fifo_p1
        fifo_r2 = 1.0 - fifo_p2

    lifo_mean = lifo_fraction * mean_total
    lifo_var = lifo_fraction * sigma_total * sigma_total
    lifo_active = lifo_mean > 0.0
    lifo_weight = 0.0
    lifo_p1 = 1.0
    lifo_p2 = 1.0
    lifo_r1 = 0.0
    lifo_r2 = 0.0
    if lifo_active:
        lifo_a = lifo_var / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        lifo_disc = lifo_a * lifo_a - 1.0
        if lifo_disc < 0.0:
            lifo_disc = 0.0
        lifo_root = lifo_disc ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_weight = 1.0 / lifo_b
        lifo_p1 = 2.0 / (2.0 + lifo_mean * lifo_b)
        lifo_p2 = 2.0 / (2.0 + lifo_mean * lifo_c)
        lifo_r1 = 1.0 - lifo_p1
        lifo_r2 = 1.0 - lifo_p2

    x = [max(0.0, float(age[i])) for i in range(m)]

    raw_position = 0.0
    for i in range(m):
        raw_position = raw_position + x[i]
    for j in range(len(pipeline)):
        raw_position = raw_position + max(0.0, float(pipeline[j]))

    for step in range(lead):
        if fifo_active:
            cumulative = 0.0
            for i in range(m):
                bucket = x[i]
                next_cumulative = cumulative + bucket
                z0 = cumulative / demand_scale
                z1 = next_cumulative / demand_scale
                e0 = demand_scale * (
                    fifo_weight * fifo_r1 * (1.0 - fifo_r1 ** z0) / fifo_p1
                    + (1.0 - fifo_weight) * fifo_r2
                    * (1.0 - fifo_r2 ** z0) / fifo_p2
                )
                e1 = demand_scale * (
                    fifo_weight * fifo_r1 * (1.0 - fifo_r1 ** z1) / fifo_p1
                    + (1.0 - fifo_weight) * fifo_r2
                    * (1.0 - fifo_r2 ** z1) / fifo_p2
                )
                taken = e1 - e0
                if taken < 0.0:
                    taken = 0.0
                if taken > bucket:
                    taken = bucket
                x[i] = bucket - taken
                cumulative = next_cumulative

        if lifo_active:
            cumulative = 0.0
            for k in range(m):
                i = m - 1 - k
                bucket = x[i]
                next_cumulative = cumulative + bucket
                z0 = cumulative / demand_scale
                z1 = next_cumulative / demand_scale
                e0 = demand_scale * (
                    lifo_weight * lifo_r1 * (1.0 - lifo_r1 ** z0) / lifo_p1
                    + (1.0 - lifo_weight) * lifo_r2
                    * (1.0 - lifo_r2 ** z0) / lifo_p2
                )
                e1 = demand_scale * (
                    lifo_weight * lifo_r1 * (1.0 - lifo_r1 ** z1) / lifo_p1
                    + (1.0 - lifo_weight) * lifo_r2
                    * (1.0 - lifo_r2 ** z1) / lifo_p2
                )
                taken = e1 - e0
                if taken < 0.0:
                    taken = 0.0
                if taken > bucket:
                    taken = bucket
                x[i] = bucket - taken
                cumulative = next_cumulative

        shifted = [0.0 for i in range(m)]
        for i in range(m - 1):
            shifted[i] = x[i + 1]
        if step < lead - 1 and step < len(pipeline):
            shifted[m - 1] = max(0.0, float(pipeline[step]))
        x = shifted

    projected_effective = 0.0
    for i in range(m):
        life_fraction = float(i + 1) / float(m)
        age_weight = W_OLD + (W_NEW - W_OLD) * life_fraction ** W_SHAPE
        if age_weight < 0.0:
            age_weight = 0.0
        projected_effective = projected_effective + age_weight * x[i]

    arrival_target = S * mean_total * float(m) / 16.0
    raw_target = arrival_target * float(m + lead) / float(m)

    raw_gap = raw_target - raw_position
    if raw_gap < 0.0:
        raw_gap = 0.0
    projected_gap = arrival_target - projected_effective
    if projected_gap < 0.0:
        projected_gap = 0.0

    q = GAIN * ((1.0 - BLEND) * raw_gap + BLEND * projected_gap)
    if not (q >= 0.0):
        return 0.0
    if q > 1000000.0:
        return 1000000.0
    return float(q)
