def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 15.0 # OPT_PARAM: {"type":"float","initial":15.0,"min":0.0,"max":60.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    W0 = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.5}
    AF = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.0,"max":3.0}
    AL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    PF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":5.0}
    PL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":5.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    pipe = 0.0
    for i in range(m):
        freshness = (i + 0.5) / m
        fifo_credit = AF * f * ((1.0 - freshness) ** PF)
        lifo_credit = AL * (1.0 - f) * (freshness ** PL)
        weight = W0 + fifo_credit + lifo_credit
        effective = effective + weight * age[i]
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    q = S - effective - WP * pipe
    return max(0.0, min(C, q))
