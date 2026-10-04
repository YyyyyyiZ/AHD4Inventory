def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    projection_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.8}
    age_floor = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}
    age_power = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.25,"max":4.0}
    order_gain = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.6}

    m = len(age)
    z = [0.0] * m
    for i in range(m):
        x = float(age[i])
        if not (x >= 0.0):
            x = 0.0
        if x > 1000000.0:
            x = 1000000.0
        z[i] = x

    fifo_mean = f * mu
    lifo_mean = (1.0 - f) * mu
    demand_variance_base = (mu * cv) ** 2

    if fifo_mean > 0.0:
        fifo_variance = f * demand_variance_base
        fifo_a = fifo_variance / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
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
    else:
        fifo_weight = 1.0
        fifo_p1 = 1.0
        fifo_p2 = 1.0
        fifo_r1 = 0.0
        fifo_r2 = 0.0

    if lifo_mean > 0.0:
        lifo_variance = (1.0 - f) * demand_variance_base
        lifo_a = lifo_variance / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
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
    else:
        lifo_weight = 1.0
        lifo_p1 = 1.0
        lifo_p2 = 1.0
        lifo_r1 = 0.0
        lifo_r2 = 0.0

    for t in range(int(L)):
        remaining = [0.0] * m
        fifo_cumulative = 0.0

        for i in range(m):
            x = z[i]
            if fifo_mean > 0.0 and x > 0.0:
                threshold0 = fifo_cumulative / projection_scale
                n0 = int(threshold0) + 1
                plus01 = (fifo_r1 ** n0) * (n0 - threshold0 + fifo_r1 / fifo_p1)
                plus02 = (fifo_r2 ** n0) * (n0 - threshold0 + fifo_r2 / fifo_p2)
                plus0 = fifo_weight * plus01 + (1.0 - fifo_weight) * plus02

                threshold1 = (fifo_cumulative + x) / projection_scale
                n1 = int(threshold1) + 1
                plus11 = (fifo_r1 ** n1) * (n1 - threshold1 + fifo_r1 / fifo_p1)
                plus12 = (fifo_r2 ** n1) * (n1 - threshold1 + fifo_r2 / fifo_p2)
                plus1 = fifo_weight * plus11 + (1.0 - fifo_weight) * plus12

                consumed = projection_scale * (plus0 - plus1)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > x:
                    consumed = x
                remaining[i] = x - consumed
            else:
                remaining[i] = x
            fifo_cumulative = fifo_cumulative + x

        lifo_cumulative = 0.0
        for k in range(m):
            i = m - 1 - k
            x = remaining[i]
            if lifo_mean > 0.0 and x > 0.0:
                threshold0 = lifo_cumulative / projection_scale
                n0 = int(threshold0) + 1
                plus01 = (lifo_r1 ** n0) * (n0 - threshold0 + lifo_r1 / lifo_p1)
                plus02 = (lifo_r2 ** n0) * (n0 - threshold0 + lifo_r2 / lifo_p2)
                plus0 = lifo_weight * plus01 + (1.0 - lifo_weight) * plus02

                threshold1 = (lifo_cumulative + x) / projection_scale
                n1 = int(threshold1) + 1
                plus11 = (lifo_r1 ** n1) * (n1 - threshold1 + lifo_r1 / lifo_p1)
                plus12 = (lifo_r2 ** n1) * (n1 - threshold1 + lifo_r2 / lifo_p2)
                plus1 = lifo_weight * plus11 + (1.0 - lifo_weight) * plus12

                consumed = projection_scale * (plus0 - plus1)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > x:
                    consumed = x
                remaining[i] = x - consumed
            lifo_cumulative = lifo_cumulative + x

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = remaining[i + 1]

        if t < int(L) - 1 and t < len(pipeline):
            arrival = float(pipeline[t])
            if not (arrival >= 0.0):
                arrival = 0.0
            if arrival > 1000000.0:
                arrival = 1000000.0
            shifted[m - 1] = arrival

        z = shifted

    effective_inventory = 0.0
    for i in range(m):
        relative_life = float(i + 1) / float(m)
        weight = age_floor + (1.0 - age_floor) * (relative_life ** age_power)
        effective_inventory = effective_inventory + weight * z[i]

    order = order_gain * (S - effective_inventory)
    if not (order > 0.0):
        return 0.0
    if order > 1000000.0:
        return 1000000.0
    return order
