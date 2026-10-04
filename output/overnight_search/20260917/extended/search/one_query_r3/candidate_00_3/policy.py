def compute_order_amount(age, pipeline, mu, cv, f, L):
    B = 8.0 # OPT_PARAM: {"type":"float","initial":8.0,"min":0.0,"max":40.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    MF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":2.5}
    ML = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":2.5}
    A = 0.4 # OPT_PARAM: {"type":"float","initial":0.4,"min":0.0,"max":3.0}
    m = len(age)
    work = [0.0 for i in range(m)]
    for i in range(m):
        work[i] = age[i]
    for step in range(L):
        remaining = MF * f * mu
        for i in range(m):
            take = min(work[i], remaining)
            work[i] = work[i] - take
            remaining = remaining - take
        remaining = ML * (1.0 - f) * mu
        for k in range(m):
            i = m - 1 - k
            take = min(work[i], remaining)
            work[i] = work[i] - take
            remaining = remaining - take
        for i in range(m - 1):
            work[i] = work[i + 1]
        work[m - 1] = 0.0
        if step < len(pipeline):
            work[m - 1] = pipeline[step]
    projected = 0.0
    for i in range(m):
        freshness = (i + 1.0) / m
        projected = projected + work[i] * (freshness ** A)
    q = B - projected
    return max(0.0, min(C, q))
