def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 26.0 # OPT_PARAM: {"type":"float","initial":26.0,"min":0.0,"max":60.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":3.0}
    R = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":1.5}
    Z = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":2.0}
    DMAX = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":2.0}
    DAVG = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    stock = 0.0
    for i in range(m):
        stock = stock + age[i]
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    cumulative = 0.0
    maximum_overload = 0.0
    average_overload = 0.0
    mix = f + R * (1.0 - f)
    variance_mix = f + R * R * (1.0 - f)
    for i in range(m):
        cumulative = cumulative + age[i]
        life = i + 1.0
        capacity_mean = K * mu * mix * life
        capacity_sd = Z * mu * cv * ((variance_mix * life) ** 0.5)
        capacity = max(0.0, capacity_mean - capacity_sd)
        overload = max(0.0, cumulative - capacity)
        maximum_overload = max(maximum_overload, overload)
        average_overload = average_overload + overload / m
    raw = S - stock - WP * pipe + DMAX * maximum_overload + DAVG * average_overload
    return max(0.0, min(C, raw))
