def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 11.0 # OPT_PARAM: {"type":"float","initial":11.0,"min":0.0,"max":40.0}
    C = 8.0 # OPT_PARAM: {"type":"float","initial":8.0,"min":0.0,"max":40.0}
    D = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    W = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":-4.0,"max":8.0}
    P = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.2,"max":6.0}

    m = len(age)
    forecast = [0.0 for i in range(m)]
    quiet = [0.0 for i in range(m)]
    for i in range(m):
        forecast[i] = float(age[i])
        quiet[i] = float(age[i])

    for t in range(L):
        remaining = D*f*mu
        for i in range(m):
            used = forecast[i]
            if used > remaining:
                used = remaining
            forecast[i] = forecast[i] - used
            remaining = remaining - used

        remaining = D*(1.0-f)*mu
        for k in range(m):
            i = m - 1 - k
            used = forecast[i]
            if used > remaining:
                used = remaining
            forecast[i] = forecast[i] - used
            remaining = remaining - used

        for i in range(m-1):
            forecast[i] = forecast[i+1]
            quiet[i] = quiet[i+1]
        if m > 0:
            forecast[m-1] = 0.0
            quiet[m-1] = 0.0
            if t < len(pipeline):
                forecast[m-1] = float(pipeline[t])
                quiet[m-1] = float(pipeline[t])

    total = 0.0
    expiry_pressure = 0.0
    for i in range(m):
        amount = (1.0-W)*forecast[i] + W*quiet[i]
        remaining_fraction = (i+1.0)/m
        age_risk = (1.0-remaining_fraction)**P
        total = total + amount
        expiry_pressure = expiry_pressure + amount*age_risk

    raw = S - K*total - A*(1.0-f)*expiry_pressure
    if raw != raw:
        return 0.0
    if raw <= 0.0:
        return 0.0
    if raw > C:
        return float(C)
    return float(raw)
