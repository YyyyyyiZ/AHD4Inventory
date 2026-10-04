def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 25.0 # OPT_PARAM: {"type":"float","initial":25.0,"min":0.0,"max":60.0}
    KF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":4.0}
    KL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":4.0}
    PA = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":2.0}
    B = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    P = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.1,"max":4.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    effective = 0.0
    for i in range(m):
        older = 0.0
        for j in range(i):
            older = older + age[j]
        younger = PA * pipe
        for j in range(i + 1, m):
            younger = younger + age[j]
        life = i + 1.0
        fifo_capacity = KF * f * mu * life + 0.001
        lifo_capacity = KL * (1.0 - f) * mu * life + 0.001
        fifo_score = fifo_capacity / (fifo_capacity + older)
        lifo_score = lifo_capacity / (lifo_capacity + younger)
        score = f * fifo_score + (1.0 - f) * lifo_score
        weight = B + (1.0 - B) * (score ** P)
        effective = effective + weight * age[i]
    raw = S - effective - WP * pipe
    return max(0.0, min(C, raw))
