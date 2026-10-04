def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 19.0 # OPT_PARAM: {"type":"float","initial":19.0,"min":0.0,"max":60.0}
    WP = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":1.5}
    RHO = 0.20 # OPT_PARAM: {"type":"float","initial":0.20,"min":0.0,"max":1.0}
    Z = -0.30 # OPT_PARAM: {"type":"float","initial":-0.30,"min":-2.5,"max":2.5}
    B = 0.90 # OPT_PARAM: {"type":"float","initial":0.90,"min":0.0,"max":2.5}
    KC = 0.80 # OPT_PARAM: {"type":"float","initial":0.80,"min":0.0,"max":2.0}
    G = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":2.5}

    m = len(age)
    age_total = 0.0
    pipeline_total = 0.0
    prefix = 0.0
    expiration_risk = 0.0

    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + float(pipeline[j])

    service_fraction = f + RHO * (1.0 - f)
    variance_fraction = f + RHO * RHO * (1.0 - f)

    for i in range(m):
        stock = float(age[i])
        age_total = age_total + stock
        prefix = prefix + stock
        horizon = float(i + 1)
        service_mean = mu * horizon * service_fraction
        service_std = mu * cv * (horizon * variance_fraction) ** 0.5
        threshold = service_mean + Z * service_std
        if threshold < 0.0:
            threshold = 0.0
        excess = prefix - threshold
        if excess > expiration_risk:
            expiration_risk = excess

    congestion_threshold = KC * mu * float(m)
    congestion = age_total + pipeline_total - congestion_threshold
    if congestion < 0.0:
        congestion = 0.0

    inventory_position = age_total + WP * pipeline_total
    q = S - inventory_position + B * expiration_risk + G * congestion
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 120.0:
        q = 120.0
    return float(q)
