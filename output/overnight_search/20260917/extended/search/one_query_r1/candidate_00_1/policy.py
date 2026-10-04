def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 25.0 # OPT_PARAM: {"type":"float","initial":25.0,"min":0.0,"max":60.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    W0 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.5}
    W1 = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":1.5}
    W2 = 0.78 # OPT_PARAM: {"type":"float","initial":0.78,"min":0.0,"max":1.5}
    W3 = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":1.5}
    W4 = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.5}
    W5 = 0.36 # OPT_PARAM: {"type":"float","initial":0.36,"min":0.0,"max":1.5}
    W6 = 0.23 # OPT_PARAM: {"type":"float","initial":0.23,"min":0.0,"max":1.5}
    W7 = 0.12 # OPT_PARAM: {"type":"float","initial":0.12,"min":0.0,"max":1.5}
    m = len(age)
    effective = 0.0
    for i in range(m):
        d = m - 1 - i
        if d == 0:
            weight = W0
        elif d == 1:
            weight = W1
        elif d == 2:
            weight = W2
        elif d == 3:
            weight = W3
        elif d == 4:
            weight = W4
        elif d == 5:
            weight = W5
        elif d == 6:
            weight = W6
        else:
            weight = W7
        effective = effective + weight * age[i]
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    raw = S - effective - WP * pipe
    return max(0.0, min(C, raw))
