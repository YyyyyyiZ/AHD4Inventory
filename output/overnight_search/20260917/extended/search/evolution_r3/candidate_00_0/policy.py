def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":40.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    A = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":3.0}
    D = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":2.5}
    H = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.0}

    m = len(age)
    work = [float(age[i]) for i in range(m)]

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + pipeline[j]

    current_effective = P * pipeline_total
    for i in range(m):
        x = (i + 1.0) / m
        current_effective = current_effective + age[i] * (x ** A)

    fifo_flow = D * f * mu
    lifo_flow = D * (1.0 - f) * mu

    for step in range(L):
        remaining = fifo_flow
        for i in range(m):
            take = min(work[i], remaining)
            work[i] = work[i] - take
            remaining = remaining - take

        remaining = lifo_flow
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

    projected_effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        projected_effective = projected_effective + work[i] * (x ** A)

    effective = (1.0 - H) * current_effective + H * projected_effective
    q = K * (S - effective)

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > C:
        q = C
    return q
