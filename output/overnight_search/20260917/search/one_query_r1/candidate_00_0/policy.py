def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":60.0}
    A1 = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.0,"max":1.5}
    A2 = 0.20 # OPT_PARAM: {"type":"float","initial":0.20,"min":0.0,"max":1.5}
    A3 = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":1.5}
    A4 = 0.90 # OPT_PARAM: {"type":"float","initial":0.90,"min":0.0,"max":1.5}
    A5 = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":1.5}
    P = 0.90 # OPT_PARAM: {"type":"float","initial":0.90,"min":0.0,"max":1.5}

    m = len(age)
    effective_inventory = 0.0

    for i in range(m):
        coefficient = A5
        if i == 0:
            coefficient = A1
        elif i == 1:
            coefficient = A2
        elif i == 2:
            coefficient = A3
        elif i == 3:
            coefficient = A4
        effective_inventory = effective_inventory + coefficient * float(age[i])

    pipeline_inventory = 0.0
    for j in range(len(pipeline)):
        pipeline_inventory = pipeline_inventory + float(pipeline[j])

    q = S - effective_inventory - P * pipeline_inventory
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 120.0:
        q = 120.0
    return float(q)
