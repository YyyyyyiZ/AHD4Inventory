def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":50.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    DM = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":4.0}
    FLOOR = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":0.8}
    BLOCK = 4.0 # OPT_PARAM: {"type":"float","initial":4.0,"min":0.0,"max":12.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    total = 0.0
    pipe = 0.0
    effective = 0.0
    prefix = 0.0
    for i in range(m):
        total = total + age[i]
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    for i in range(m):
        r = i + 1.0
        rank_fifo = prefix + 0.5 * age[i]
        younger = total - prefix - age[i]
        rank_lifo = younger + 0.5 * age[i]
        for j in range(len(pipeline)):
            if j + 1.0 < r:
                rank_lifo = rank_lifo + pipeline[j]
        rank_lifo = rank_lifo + BLOCK * max(0.0, r - L)
        if f > 0.0:
            mean_fifo = DM * f * mu * r
            var_fifo = r * f * (mu * cv) * (mu * cv)
            z_fifo = (mean_fifo - rank_fifo) / (1.0 + var_fifo ** 0.5)
            p_fifo = 0.5 + 0.5 * z_fifo / (K + abs(z_fifo))
        else:
            p_fifo = 0.0
        if f < 1.0:
            mean_lifo = DM * (1.0 - f) * mu * r
            var_lifo = r * (1.0 - f) * (mu * cv) * (mu * cv)
            z_lifo = (mean_lifo - rank_lifo) / (1.0 + var_lifo ** 0.5)
            p_lifo = 0.5 + 0.5 * z_lifo / (K + abs(z_lifo))
        else:
            p_lifo = 0.0
        p_use = 1.0 - (1.0 - p_fifo) * (1.0 - p_lifo)
        credit = FLOOR + (1.0 - FLOOR) * p_use
        effective = effective + credit * age[i]
        prefix = prefix + age[i]
    q = S - effective - WP * pipe
    return max(0.0, min(C, q))
