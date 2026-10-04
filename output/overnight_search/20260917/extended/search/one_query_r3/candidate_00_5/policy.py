def compute_order_amount(age, pipeline, mu, cv, f, L):
    Q = 4.0 # OPT_PARAM: {"type":"float","initial":4.0,"min":0.0,"max":15.0}
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":50.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    K = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}
    R = 0.02 # OPT_PARAM: {"type":"float","initial":0.02,"min":0.0,"max":0.5}
    A = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.05,"max":4.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    pipe = 0.0
    for i in range(m):
        freshness = (i + 1.0) / m
        effective = effective + age[i] * (freshness ** A)
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    gap = S - effective - WP * pipe
    correction = K * gap / (1.0 + R * abs(gap))
    q = Q + correction
    return max(0.0, min(C, q))
