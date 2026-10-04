def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    age_power = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":4.0}
    floor_credit = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":0.0,"max":1.5}
    fifo_rate = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    lifo_rate = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    age_weight = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":4.0}
    flow_weight = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":4.0}
    m = len(age)
    total = 0.0
    effective = 0.0
    x = [0.0] * m
    for i in range(m):
        total = total + age[i]
        x[i] = float(age[i])
        relative_age = (i + 1.0) / m
        credit = floor_credit + (1.0 - floor_credit) * (relative_age ** age_power)
        effective = effective + age[i] * credit
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    for t in range(L):
        if t > 0 and t - 1 < len(pipeline):
            x[m - 1] = x[m - 1] + pipeline[t - 1]
        remaining_fifo = fifo_rate * f * mu
        for i in range(m):
            take = min(x[i], remaining_fifo)
            x[i] = x[i] - take
            remaining_fifo = remaining_fifo - take
        remaining_lifo = lifo_rate * (1.0 - f) * mu
        for k in range(m):
            i = m - 1 - k
            take = min(x[i], remaining_lifo)
            x[i] = x[i] - take
            remaining_lifo = remaining_lifo - take
        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0
    survivors = 0.0
    for i in range(m):
        survivors = survivors + x[i]
    position_signal = max(0.0, S - total - pipe)
    age_signal = max(0.0, S - effective - pipe)
    flow_signal = max(0.0, S - survivors)
    denominator = 1.0 + age_weight + flow_weight
    raw = (position_signal + age_weight * age_signal + flow_weight * flow_signal) / denominator
    return max(0.0, min(C, raw))
