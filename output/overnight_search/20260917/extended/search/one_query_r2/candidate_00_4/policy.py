def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    age_power = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":4.0}
    pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    stale_gate = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":8.0}
    stale_power = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.25,"max":5.0}
    smoothing = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":0.9}
    m = len(age)
    effective = 0.0
    stale = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        effective = effective + age[i] * (x ** age_power)
        stale = stale + age[i] * ((1.0 - x) ** stale_power)
    pipe = 0.0
    previous_order = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
        if j == len(pipeline) - 1:
            previous_order = pipeline[j]
    base = max(0.0, S - effective - pipeline_credit * pipe)
    gate = 1.0 / (1.0 + stale_gate * (1.0 - f) * stale / (mu + 1.0e-9))
    gated = base * gate
    raw = (1.0 - smoothing) * gated + smoothing * previous_order
    return max(0.0, min(C, raw))
