def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    A = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.01,"max":3.0}
    F = 0.02 # OPT_PARAM: {"type":"float","initial":0.02,"min":0.0,"max":0.95}
    B = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-1.0,"max":3.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":2.5}
    K = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-1.0,"max":2.0}
    m = len(age)
    target = S - 3.4 * (cv - 1.75) - 1.4 * f + 1.0 * (m - 7)
    power = A + 1.8 * f
    effective = 0.0
    old_load = 0.0
    for i in range(m):
        t = (i + 1.0) / m
        weight = F + (1.0 - F) * (t ** power) * (1.0 + B * (1.0 - t))
        effective = effective + weight * age[i]
        old_load = old_load + (1.0 - t) * age[i]
    for j in range(len(pipeline)):
        effective = effective + P * pipeline[j]
    scale = max(1.0, target + mu * m)
    effective = effective + K * old_load * old_load / scale
    gap = target - effective
    order = G * gap
    return max(0.0, min(C, order))
