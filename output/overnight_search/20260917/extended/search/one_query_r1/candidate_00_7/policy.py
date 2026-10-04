def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    C = 28.0 # OPT_PARAM: {"type":"float","initial":28.0,"min":0.0,"max":60.0}
    A = 0.45 # OPT_PARAM: {"type":"float","initial":0.45,"min":0.0,"max":4.0}
    B = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    LOW = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    HF = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.0,"max":5.0}
    HL = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.0,"max":5.0}
    W0 = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.001,"max":2.0}
    W1 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.001,"max":2.0}
    W2 = 0.12 # OPT_PARAM: {"type":"float","initial":0.12,"min":0.001,"max":2.0}
    W3 = 0.12 # OPT_PARAM: {"type":"float","initial":0.12,"min":0.001,"max":2.0}
    W4 = 0.06 # OPT_PARAM: {"type":"float","initial":0.06,"min":0.001,"max":2.0}
    m = len(age)
    weighted_gap = 0.0
    weight_total = 0.0
    for scenario in range(5):
        if scenario == 0:
            scale_f = LOW
            scale_l = LOW
            scenario_weight = W0
        elif scenario == 1:
            scale_f = 1.0
            scale_l = 1.0
            scenario_weight = W1
        elif scenario == 2:
            scale_f = 1.0 + HF * cv
            scale_l = 1.0
            scenario_weight = W2
        elif scenario == 3:
            scale_f = 1.0
            scale_l = 1.0 + HL * cv
            scenario_weight = W3
        else:
            scale_f = 1.0 + HF * cv
            scale_l = 1.0 + HL * cv
            scenario_weight = W4
        work = [0.0] * m
        for i in range(m):
            work[i] = age[i]
        for step in range(L):
            fifo_left = scale_f * f * mu
            for i in range(m):
                take = min(work[i], fifo_left)
                work[i] = work[i] - take
                fifo_left = fifo_left - take
            lifo_left = scale_l * (1.0 - f) * mu
            for k in range(m):
                i = m - 1 - k
                take = min(work[i], lifo_left)
                work[i] = work[i] - take
                lifo_left = lifo_left - take
            nxt = [0.0] * m
            for i in range(m - 1):
                nxt[i] = work[i + 1]
            if step < len(pipeline):
                nxt[m - 1] = pipeline[step]
            else:
                nxt[m - 1] = 0.0
            work = nxt
        effective = 0.0
        for i in range(m):
            x = (i + 1.0) / m
            weight = B + (1.0 - B) * (x ** A)
            effective = effective + weight * work[i]
        gap = max(0.0, S - effective)
        weighted_gap = weighted_gap + scenario_weight * gap
        weight_total = weight_total + scenario_weight
    raw = weighted_gap / weight_total
    return max(0.0, min(C, raw))
