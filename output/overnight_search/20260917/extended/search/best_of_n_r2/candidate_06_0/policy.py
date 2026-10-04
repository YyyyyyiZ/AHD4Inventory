def compute_order_amount(age, pipeline, mu, cv, f, L):
    target = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":30.0}
    response = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":3.0}
    demand_factor = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    old_credit = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.5}
    age_curve = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":5.0}
    order_limit = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":40.0}
    m = len(age)
    work = [max(0.0, float(age[i])) for i in range(m)]
    demand_scale = demand_factor / max(float(cv), 0.01)
    fifo_forecast = max(0.0, float(mu) * float(f) * demand_scale)
    lifo_forecast = max(0.0, float(mu) * (1.0 - float(f)) * demand_scale)
    for step in range(L):
        fifo_left = fifo_forecast
        for i in range(m):
            used = min(work[i], fifo_left)
            work[i] = work[i] - used
            fifo_left = fifo_left - used
        lifo_left = lifo_forecast
        for i in range(m):
            j = m - 1 - i
            used = min(work[j], lifo_left)
            work[j] = work[j] - used
            lifo_left = lifo_left - used
        shifted = [0.0 for i in range(m)]
        for i in range(m - 1):
            shifted[i] = work[i + 1]
        if step < len(pipeline):
            shifted[m - 1] = max(0.0, float(pipeline[step]))
        work = shifted
    effective = 0.0
    for i in range(m):
        relative_life = float(i + 1) / float(m)
        weight = old_credit + (1.0 - old_credit) * relative_life ** age_curve
        effective = effective + weight * work[i]
    order = response * max(0.0, target - effective)
    return max(0.0, min(order_limit, order))
