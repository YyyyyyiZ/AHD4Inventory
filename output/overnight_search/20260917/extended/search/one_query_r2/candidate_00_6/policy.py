def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    oldest_credit = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":2.0}
    lower_credit = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":2.0}
    upper_credit = 0.95 # OPT_PARAM: {"type":"float","initial":0.95,"min":0.0,"max":2.0}
    youngest_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        x = i / max(1.0, m - 1.0)
        if x < 1.0 / 3.0:
            z = 3.0 * x
            weight = oldest_credit * (1.0 - z) + lower_credit * z
        elif x < 2.0 / 3.0:
            z = 3.0 * x - 1.0
            weight = lower_credit * (1.0 - z) + upper_credit * z
        else:
            z = 3.0 * x - 2.0
            weight = upper_credit * (1.0 - z) + youngest_credit * z
        effective = effective + age[i] * weight
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    raw = S - effective - pipeline_credit * pipe
    return max(0.0, min(C, raw))
