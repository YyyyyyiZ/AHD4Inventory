def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 22.0 # OPT_PARAM: {"type":"float","initial":22.0,"min":0.0,"max":60.0}
    CP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    WOLD = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":-0.5,"max":1.5}
    WYOUNG = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    GAMMA = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.2,"max":4.0}
    m = len(age)
    credited = 0.0
    i = 0
    for i in range(m):
        relative_life = float(i + 1) / float(m)
        weight = WOLD + (WYOUNG - WOLD) * relative_life ** GAMMA
        credited = credited + weight * float(age[i])
    pipe_total = 0.0
    j = 0
    for j in range(len(pipeline)):
        pipe_total = pipe_total + float(pipeline[j])
    q = S - credited - CP * pipe_total
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
