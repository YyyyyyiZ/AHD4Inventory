def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    W0 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":1.5}
    WM = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":1.5}
    W1 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.5}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    pipe = 0.0
    for i in range(m):
        z = (i + 0.5) / m
        if z < 0.5:
            weight = W0 + (WM - W0) * (z / 0.5)
        else:
            weight = WM + (W1 - WM) * ((z - 0.5) / 0.5)
        effective = effective + weight * age[i]
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    q = S - effective - WP * pipe
    return max(0.0, min(C, q))
