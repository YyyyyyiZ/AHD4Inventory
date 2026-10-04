def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    W_old = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":3.0}
    W_mid = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":3.0}
    D = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.5}
    E = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":3.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        if m > 1:
            x = i / (m - 1.0)
        else:
            x = 1.0
        if x <= 0.5:
            weight = W_old + (W_mid - W_old) * (2.0 * x)
        else:
            weight = W_mid + (1.0 - W_mid) * (2.0 * x - 1.0)
        effective = effective + weight * age[i]
    pipeline_total = 0.0
    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + pipeline[j]
    threatened = 0.0
    expiry_pressure = 0.0
    for i in range(m):
        if i >= L:
            threatened = threatened + age[i]
            clearance = D * mu * (i + 1.0 - L)
            excess = threatened - clearance
            if excess > expiry_pressure:
                expiry_pressure = excess
    if expiry_pressure < 0.0:
        expiry_pressure = 0.0
    lifo_share = 1.0 - f
    if lifo_share < 0.0:
        lifo_share = 0.0
    gap = S - effective - pipeline_total - E * lifo_share * expiry_pressure
    if gap < 0.0:
        gap = 0.0
    if gap > C:
        gap = C
    return float(gap)
