def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    alpha = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":4.0}
    floor_credit = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.5}
    pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        weight = floor_credit + (1.0 - floor_credit) * (x ** alpha)
        effective = effective + age[i] * weight
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    raw = S - effective - pipeline_credit * pipe
    return max(0.0, min(C, raw))
