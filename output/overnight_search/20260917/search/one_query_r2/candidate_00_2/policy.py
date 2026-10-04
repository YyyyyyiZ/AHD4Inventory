def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":60.0}
    SFIFO = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":4.0}
    SLIFO = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":4.0}
    ZFIFO = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.5,"max":2.5}
    ZLIFO = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.5,"max":2.5}
    CAGE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    CPIPE = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":2.0}
    m = len(age)
    total_age = 0.0
    i = 0
    for i in range(m):
        total_age = total_age + float(age[i])
    pipe_total = 0.0
    j = 0
    for j in range(len(pipeline)):
        pipe_total = pipe_total + float(pipeline[j])
    mean_fifo = float(L) * f * mu
    mean_lifo = float(L) * (1.0 - f) * mu
    sd_fifo = (float(L) * f) ** 0.5 * mu * cv
    sd_lifo = (float(L) * (1.0 - f)) ** 0.5 * mu * cv
    den_fifo = SFIFO * sd_fifo + 0.25
    den_lifo = SLIFO * sd_lifo + 0.25
    cumulative_old = 0.0
    effective_age = 0.0
    i = 0
    for i in range(m):
        x = float(age[i])
        cumulative_old = cumulative_old + x
        cumulative_young = total_age - cumulative_old + x
        if i + 1 > L:
            threshold_fifo = cumulative_old - 0.5 * x
            threshold_lifo = cumulative_young + pipe_total - 0.5 * x
            z_fifo = (threshold_fifo - mean_fifo) / den_fifo - ZFIFO
            z_lifo = (threshold_lifo - mean_lifo) / den_lifo - ZLIFO
            if z_fifo > 40.0:
                z_fifo = 40.0
            if z_fifo < -40.0:
                z_fifo = -40.0
            if z_lifo > 40.0:
                z_lifo = 40.0
            if z_lifo < -40.0:
                z_lifo = -40.0
            survive_fifo = 1.0 / (1.0 + 2.718281828459045 ** (-z_fifo))
            survive_lifo = 1.0 / (1.0 + 2.718281828459045 ** (-z_lifo))
            effective_age = effective_age + x * survive_fifo * survive_lifo
    q = S - CAGE * effective_age - CPIPE * pipe_total
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
