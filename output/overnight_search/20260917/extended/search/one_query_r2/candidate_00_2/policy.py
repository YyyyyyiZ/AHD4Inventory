def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    risk = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":4.0}
    shape = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.25,"max":8.0}
    floor_credit = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":1.0}
    pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        older = 0.0
        for j in range(i):
            older = older + age[j]
        younger = 0.0
        for j in range(i + 1, m):
            younger = younger + age[j]
        midpoint = 0.5 * age[i]
        horizon = i + 1.0
        fifo_capacity = f * mu * horizon + risk * mu * cv * ((f * horizon) ** 0.5)
        lifo_share = 1.0 - f
        lifo_capacity = lifo_share * mu * horizon + risk * mu * cv * ((lifo_share * horizon) ** 0.5)
        fifo_probability = 0.0
        lifo_probability = 0.0
        if fifo_capacity > 0.0:
            fifo_ratio = (older + midpoint) / (fifo_capacity + 1.0e-9)
            fifo_probability = 1.0 / (1.0 + fifo_ratio ** shape)
        if lifo_capacity > 0.0:
            lifo_ratio = (younger + midpoint) / (lifo_capacity + 1.0e-9)
            lifo_probability = 1.0 / (1.0 + lifo_ratio ** shape)
        sell_probability = 1.0 - (1.0 - fifo_probability) * (1.0 - lifo_probability)
        credit = floor_credit + (1.0 - floor_credit) * sell_probability
        effective = effective + age[i] * credit
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    raw = S - effective - pipeline_credit * pipe
    return max(0.0, min(C, raw))
