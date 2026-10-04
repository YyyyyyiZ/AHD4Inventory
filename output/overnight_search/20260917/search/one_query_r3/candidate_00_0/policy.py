def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 22.0 # OPT_PARAM: {"type":"float","initial":22.0,"min":0.0,"max":60.0}
    pipeline_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    age_floor = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.2}
    age_power = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.15,"max":5.0}
    lifo_tilt = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":1.5}
    replacement_gain = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.0}

    m = len(age)
    effective_stock = 0.0
    vulnerable_stock = 0.0

    for i in range(m):
        x = age[i]
        if x < 0.0:
            x = 0.0
        relative_life = (i + 1.0) / m
        life_weight = age_floor + (1.0 - age_floor) * relative_life ** age_power
        mix_weight = 1.0 - lifo_tilt * (1.0 - f) * (1.0 - relative_life)
        if mix_weight < 0.0:
            mix_weight = 0.0
        effective_stock = effective_stock + x * life_weight * mix_weight
        vulnerable_stock = vulnerable_stock + x * (1.0 - relative_life) * (1.0 - f)

    pipeline_stock = 0.0
    for j in range(len(pipeline)):
        x = pipeline[j]
        if x > 0.0:
            pipeline_stock = pipeline_stock + x

    q = S - effective_stock - pipeline_weight * pipeline_stock
    q = q + replacement_gain * vulnerable_stock

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
