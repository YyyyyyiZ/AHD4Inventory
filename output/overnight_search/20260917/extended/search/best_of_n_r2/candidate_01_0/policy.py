def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 15.5 # OPT_PARAM: {"type":"float","initial":15.5,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    W_DOOM = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":0.0,"max":4.0}
    W_EARLY = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":0.0,"max":4.0}
    W_MID = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":4.0}
    W_FRESH = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W_PIPE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    K_BLOCK = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":8.0}

    m = len(age)
    effective = 0.0
    old_risk = 0.0
    young_cover = 0.0

    for i in range(m):
        stock = age[i]
        if i < L:
            effective = effective + W_DOOM * stock
        else:
            denominator = float(max(1, m - L))
            x = float(i + 1 - L) / denominator
            one_minus_x = 1.0 - x
            weight = (W_EARLY * one_minus_x * one_minus_x
                      + 2.0 * W_MID * x * one_minus_x
                      + W_FRESH * x * x)
            effective = effective + weight * stock
            old_risk = old_risk + one_minus_x * stock
            young_cover = young_cover + x * stock

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        pipeline_total = pipeline_total + pipeline[j]

    effective = effective + W_PIPE * pipeline_total
    young_cover = young_cover + pipeline_total

    scale = mu * float(max(1, m))
    blocking = K_BLOCK * max(0.0, 1.0 - f) * old_risk * young_cover / scale
    raw = S - effective - blocking

    if not (raw == raw):
        return 0.0
    if raw <= 0.0:
        return 0.0
    if raw >= C:
        return C
    return raw
