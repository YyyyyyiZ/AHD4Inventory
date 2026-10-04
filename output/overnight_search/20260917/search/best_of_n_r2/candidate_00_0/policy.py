def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":2.5}
    AGE_FLOOR = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}
    AGE_POWER = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.2,"max":6.0}

    m = len(age)
    projected = [0.0] * m
    for i in range(m):
        x = float(age[i])
        if x < 0.0:
            x = 0.0
        projected[i] = x

    mu_cv = mu * cv

    fifo_active = f > 0.0
    if fifo_active:
        fifo_mean = f * mu
        fifo_var = f * mu_cv * mu_cv
        fifo_a = fifo_var / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        fifo_disc = fifo_a * fifo_a - 1.0
        if fifo_disc < 0.0:
            fifo_disc = 0.0
        fifo_root = fifo_disc ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_w1 = 1.0 / fifo_b
        fifo_w2 = 1.0 - fifo_w1
        fifo_p1 = 2.0 / (2.0 + fifo_mean * fifo_b)
        fifo_p2 = 2.0 / (2.0 + fifo_mean * fifo_c)
        fifo_r1 = 1.0 - fifo_p1
        fifo_r2 = 1.0 - fifo_p2

    lifo_share = 1.0 - f
    lifo_active = lifo_share > 0.0
    if lifo_active:
        lifo_mean = lifo_share * mu
        lifo_var = lifo_share * mu_cv * mu_cv
        lifo_a = lifo_var / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        lifo_disc = lifo_a * lifo_a - 1.0
        if lifo_disc < 0.0:
            lifo_disc = 0.0
        lifo_root = lifo_disc ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_w1 = 1.0 / lifo_b
        lifo_w2 = 1.0 - lifo_w1
        lifo_p1 = 2.0 / (2.0 + lifo_mean * lifo_b)
        lifo_p2 = 2.0 / (2.0 + lifo_mean * lifo_c)
        lifo_r1 = 1.0 - lifo_p1
        lifo_r2 = 1.0 - lifo_p2

    for step in range(L):
        if step > 0:
            pipe_index = step - 1
            if pipe_index < len(pipeline):
                arrival = float(pipeline[pipe_index])
                if arrival > 0.0:
                    projected[m - 1] = projected[m - 1] + arrival

        if fifo_active:
            cumulative = 0.0
            for i in range(m):
                stock = projected[i]

                k0 = int(cumulative) + 1
                ex01 = (fifo_r1 ** k0) * (k0 - cumulative + fifo_r1 / fifo_p1)
                ex02 = (fifo_r2 ** k0) * (k0 - cumulative + fifo_r2 / fifo_p2)
                excess0 = fifo_w1 * ex01 + fifo_w2 * ex02

                endpoint = cumulative + stock
                k1 = int(endpoint) + 1
                ex11 = (fifo_r1 ** k1) * (k1 - endpoint + fifo_r1 / fifo_p1)
                ex12 = (fifo_r2 ** k1) * (k1 - endpoint + fifo_r2 / fifo_p2)
                excess1 = fifo_w1 * ex11 + fifo_w2 * ex12

                used = excess0 - excess1
                if used < 0.0:
                    used = 0.0
                if used > stock:
                    used = stock
                projected[i] = stock - used
                cumulative = endpoint

        if lifo_active:
            cumulative = 0.0
            for offset in range(m):
                i = m - 1 - offset
                stock = projected[i]

                k0 = int(cumulative) + 1
                ex01 = (lifo_r1 ** k0) * (k0 - cumulative + lifo_r1 / lifo_p1)
                ex02 = (lifo_r2 ** k0) * (k0 - cumulative + lifo_r2 / lifo_p2)
                excess0 = lifo_w1 * ex01 + lifo_w2 * ex02

                endpoint = cumulative + stock
                k1 = int(endpoint) + 1
                ex11 = (lifo_r1 ** k1) * (k1 - endpoint + lifo_r1 / lifo_p1)
                ex12 = (lifo_r2 ** k1) * (k1 - endpoint + lifo_r2 / lifo_p2)
                excess1 = lifo_w1 * ex11 + lifo_w2 * ex12

                used = excess0 - excess1
                if used < 0.0:
                    used = 0.0
                if used > stock:
                    used = stock
                projected[i] = stock - used
                cumulative = endpoint

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = projected[i + 1]
        projected = shifted

    effective_stock = 0.0
    if m > 1:
        denominator = float(m - 1)
        for i in range(m):
            relative_age = float(i) / denominator
            weight = AGE_FLOOR + (1.0 - AGE_FLOOR) * (relative_age ** AGE_POWER)
            effective_stock = effective_stock + weight * projected[i]
    elif m == 1:
        effective_stock = projected[0]

    q = GAIN * (S - effective_stock)
    if q < 0.0 or q != q:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
