def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 25.0 # OPT_PARAM: {"type":"float","initial":25.0,"min":0.0,"max":60.0}
    D = 0.65 # OPT_PARAM: {"type":"float","initial":0.65,"min":0.0,"max":1.5}
    P = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.1,"max":5.0}
    T = 2.5 # OPT_PARAM: {"type":"float","initial":2.5,"min":0.0,"max":30.0}
    H = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":2.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    total = 0.0
    pressure = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        total = total + age[i]
        pressure = pressure + age[i] * ((1.0 - x) ** P)
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    congestion = max(0.0, pressure - T)
    raw = S - total - WP * pipe + D * pressure + H * congestion
    return max(0.0, min(C, raw))
