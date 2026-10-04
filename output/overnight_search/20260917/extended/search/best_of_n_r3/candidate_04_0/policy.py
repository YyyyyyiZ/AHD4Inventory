def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    A = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-2.0,"max":4.0}
    B = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-0.9,"max":8.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    D = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":4.0}
    m = len(age)
    effective = 0.0
    pipeline_total = 0.0
    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + pipeline[j]
    effective = P * pipeline_total
    for i in range(m):
        r = (i + 1.0) / m
        weight = (r ** A) * (1.0 + B * (1.0 - r) * (1.0 - r))
        effective = effective + weight * age[i]
    doomed = 0.0
    cumulative_old = 0.0
    for k in range(1, m + 1):
        cumulative_old = cumulative_old + age[k - 1]
        younger = 0.0
        for i in range(k, m):
            younger = younger + age[i]
        for j in range(len(pipeline)):
            if j + 1 < k:
                younger = younger + pipeline[j]
        reliable_fifo = k * mu * f / cv
        reliable_lifo = k * mu * (1.0 - f) / cv
        lifo_reaching_old = reliable_lifo - younger
        if lifo_reaching_old < 0.0:
            lifo_reaching_old = 0.0
        excess = cumulative_old - reliable_fifo - lifo_reaching_old
        if excess > doomed:
            doomed = excess
    gap = S - effective + D * doomed
    order = G * gap
    if order < 0.0:
        order = 0.0
    if order > C:
        order = C
    return float(order)
