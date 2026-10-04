def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    C = 25.0 # OPT_PARAM: {"type":"float","initial":25.0,"min":0.0,"max":60.0}
    KF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    KL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    A = 0.45 # OPT_PARAM: {"type":"float","initial":0.45,"min":0.0,"max":4.0}
    B = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.0}
    m = len(age)
    work = [0.0] * m
    for i in range(m):
        work[i] = age[i]
    for step in range(L):
        fifo_left = KF * f * mu
        for i in range(m):
            take = min(work[i], fifo_left)
            work[i] = work[i] - take
            fifo_left = fifo_left - take
        lifo_left = KL * (1.0 - f) * mu
        for k in range(m):
            i = m - 1 - k
            take = min(work[i], lifo_left)
            work[i] = work[i] - take
            lifo_left = lifo_left - take
        nxt = [0.0] * m
        for i in range(m - 1):
            nxt[i] = work[i + 1]
        if step < len(pipeline):
            nxt[m - 1] = pipeline[step]
        else:
            nxt[m - 1] = 0.0
        work = nxt
    effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        weight = B + (1.0 - B) * (x ** A)
        effective = effective + weight * work[i]
    raw = S - effective
    return max(0.0, min(C, raw))
