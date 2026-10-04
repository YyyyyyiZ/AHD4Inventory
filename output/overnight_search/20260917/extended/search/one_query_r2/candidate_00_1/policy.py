def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    fifo_rate = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    lifo_rate = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    survivor_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    x = [0.0] * m
    for i in range(m):
        x[i] = float(age[i])
    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + pipeline[t - 1]
        remaining_fifo = fifo_rate * f * mu
        for i in range(m):
            take = min(x[i], remaining_fifo)
            x[i] = x[i] - take
            remaining_fifo = remaining_fifo - take
        remaining_lifo = lifo_rate * (1.0 - f) * mu
        for k in range(m):
            i = m - 1 - k
            take = min(x[i], remaining_lifo)
            x[i] = x[i] - take
            remaining_lifo = remaining_lifo - take
        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0
    survivors = 0.0
    for i in range(m):
        survivors = survivors + x[i]
    raw = S - survivor_credit * survivors
    return max(0.0, min(C, raw))
