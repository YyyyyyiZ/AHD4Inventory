def compute_order_amount(age, pipeline, mu, cv, f, L):
    target_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.3,"max":1.8}
    skew_strength = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    target_shift = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-15.0,"max":15.0}
    probability_power = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":4.0}
    old_stock_floor = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.0}
    pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}

    m = len(age)
    zero_probability = 1.0

    for stream_index in range(2):
        g = f
        if stream_index == 1:
            g = 1.0 - f

        if g > 0.0:
            M = g * mu
            V = g * (mu * cv) ** 2
            a = V / (M * M) - 1.0 / M
            if a < 1.0:
                a = 1.0
            root = (a * a - 1.0) ** 0.5
            b = 1.0 + a + root
            c = 1.0 + a - root
            weight1 = 1.0 / b
            success1 = 2.0 / (2.0 + M * b)
            success2 = 2.0 / (2.0 + M * c)
            stream_zero = weight1 * success1 + (1.0 - weight1) * success2
            zero_probability = zero_probability * stream_zero

    if zero_probability < 0.0:
        zero_probability = 0.0
    if zero_probability > 1.0:
        zero_probability = 1.0

    protection_horizon = m + L
    shape = protection_horizon / (cv * cv)
    median_factor = 1.0 - skew_strength / (9.0 * shape)
    if median_factor < 0.0:
        median_factor = 0.0

    approximate_median = protection_horizon * mu * median_factor ** 3
    target = target_scale * approximate_median + target_shift

    full_life_sale_probability = 1.0 - zero_probability ** m
    if full_life_sale_probability < 0.000001:
        full_life_sale_probability = 0.000001

    effective_stock = 0.0
    for i in range(m):
        x = age[i]
        if x < 0.0:
            x = 0.0
        remaining_life = i + 1
        sale_probability = 1.0 - zero_probability ** remaining_life
        relative_probability = sale_probability / full_life_sale_probability
        if relative_probability > 1.0:
            relative_probability = 1.0
        weight = old_stock_floor
        weight = weight + (1.0 - old_stock_floor) * relative_probability ** probability_power
        effective_stock = effective_stock + x * weight

    pipeline_stock = 0.0
    for j in range(len(pipeline)):
        x = pipeline[j]
        if x > 0.0:
            pipeline_stock = pipeline_stock + x

    q = target - effective_stock - pipeline_credit * pipeline_stock

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
