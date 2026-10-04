def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    A = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.05,"max":4.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    pipe = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        effective = effective + age[i] * (x ** A)
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    q = S - effective - P * pipe
    return max(0.0, min(C, q))
