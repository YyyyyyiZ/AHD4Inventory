def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    G = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":2.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    W_old = 1.3 # OPT_PARAM: {"type":"float","initial":1.3,"min":0.0,"max":4.0}
    W_mid = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W_new = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":4.0}
    R = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":1.75}

    m = len(age)
    x = [0.0] * m
    for i in range(m):
        x[i] = max(0.0, float(age[i]))

    mean_fifo = f * mu
    var_fifo = f * (mu * cv) * (mu * cv)
    fifo_active = mean_fifo > 0.0
    fifo_weight = 0.0
    fifo_r1 = 0.0
    fifo_r2 = 0.0
    if fifo_active:
        fifo_a = var_fifo / (mean_fifo * mean_fifo) - 1.0 / mean_fifo
        fifo_root = max(0.0, fifo_a * fifo_a - 1.0) ** 0.5
        fifo_b = 1.0 + fifo_a + fifo_root
        fifo_c = 1.0 + fifo_a - fifo_root
        fifo_weight = 1.0 / fifo_b
        fifo_p1 = 2.0 / (2.0 + mean_fifo * fifo_b)
        fifo_p2 = 2.0 / (2.0 + mean_fifo * fifo_c)
        fifo_r1 = 1.0 - fifo_p1
        fifo_r2 = 1.0 - fifo_p2

    mean_lifo = (1.0 - f) * mu
    var_lifo = (1.0 - f) * (mu * cv) * (mu * cv)
    lifo_active = mean_lifo > 0.0
    lifo_weight = 0.0
    lifo_r1 = 0.0
    lifo_r2 = 0.0
    if lifo_active:
        lifo_a = var_lifo / (mean_lifo * mean_lifo) - 1.0 / mean_lifo
        lifo_root = max(0.0, lifo_a * lifo_a - 1.0) ** 0.5
        lifo_b = 1.0 + lifo_a + lifo_root
        lifo_c = 1.0 + lifo_a - lifo_root
        lifo_weight = 1.0 / lifo_b
        lifo_p1 = 2.0 / (2.0 + mean_lifo * lifo_b)
        lifo_p2 = 2.0 / (2.0 + mean_lifo * lifo_c)
        lifo_r1 = 1.0 - lifo_p1
        lifo_r2 = 1.0 - lifo_p2

    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + max(0.0, float(pipeline[t - 1]))

        if fifo_active:
            prior = 0.0
            for i in range(m):
                quantity = x[i]
                upper = prior + quantity
                h_prior = fifo_weight * fifo_r1 * (1.0 - fifo_r1 ** prior) / (1.0 - fifo_r1)
                h_prior = h_prior + (1.0 - fifo_weight) * fifo_r2 * (1.0 - fifo_r2 ** prior) / (1.0 - fifo_r2)
                h_upper = fifo_weight * fifo_r1 * (1.0 - fifo_r1 ** upper) / (1.0 - fifo_r1)
                h_upper = h_upper + (1.0 - fifo_weight) * fifo_r2 * (1.0 - fifo_r2 ** upper) / (1.0 - fifo_r2)
                consumed = min(quantity, max(0.0, R * (h_upper - h_prior)))
                x[i] = quantity - consumed
                prior = upper

        if lifo_active:
            prior = 0.0
            for k in range(m):
                i = m - 1 - k
                quantity = x[i]
                upper = prior + quantity
                h_prior = lifo_weight * lifo_r1 * (1.0 - lifo_r1 ** prior) / (1.0 - lifo_r1)
                h_prior = h_prior + (1.0 - lifo_weight) * lifo_r2 * (1.0 - lifo_r2 ** prior) / (1.0 - lifo_r2)
                h_upper = lifo_weight * lifo_r1 * (1.0 - lifo_r1 ** upper) / (1.0 - lifo_r1)
                h_upper = h_upper + (1.0 - lifo_weight) * lifo_r2 * (1.0 - lifo_r2 ** upper) / (1.0 - lifo_r2)
                consumed = min(quantity, max(0.0, R * (h_upper - h_prior)))
                x[i] = quantity - consumed
                prior = upper

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0

    effective = 0.0
    for i in range(m):
        if m > 1:
            r = float(i) / float(m - 1)
        else:
            r = 1.0
        one_minus_r = 1.0 - r
        weight = one_minus_r * one_minus_r * W_old
        weight = weight + 2.0 * r * one_minus_r * W_mid
        weight = weight + r * r * W_new
        effective = effective + weight * x[i]

    gap = S - effective
    if gap <= 0.0:
        return 0.0
    order = K * gap + G * gap * gap / (S + 1.0)
    return max(0.0, min(C, order))
