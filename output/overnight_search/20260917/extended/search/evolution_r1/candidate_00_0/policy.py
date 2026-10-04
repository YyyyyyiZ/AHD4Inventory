def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 15.0 # OPT_PARAM: {"type":"float","initial":15.0,"min":0.0,"max":60.0}
    C = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":30.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    a = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":4.0}
    R = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        weight = ((i + 1.0) / m) ** a
        if i < L:
            weight = weight * R
        effective = effective + weight * age[i]
    projected_pipeline = 0.0
    for j in range(len(pipeline)):
        projected_pipeline = projected_pipeline + pipeline[j]
    order = S - K * effective - P * projected_pipeline
    return max(0.0, min(C, order))
