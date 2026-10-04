def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    A = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":4.0}
    F = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.0,"max":1.0}
    W = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        weight = F + (1.0 - F) * (x ** A)
        effective = effective + weight * age[i]
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    raw = S - effective - W * pipe
    return max(0.0, min(C, raw))
