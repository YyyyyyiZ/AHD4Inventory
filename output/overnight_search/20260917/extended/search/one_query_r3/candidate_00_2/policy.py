def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    H = 2.5 # OPT_PARAM: {"type":"float","initial":2.5,"min":0.25,"max":10.0}
    P = 3.0 # OPT_PARAM: {"type":"float","initial":3.0,"min":0.25,"max":8.0}
    A = 0.9 # OPT_PARAM: {"type":"float","initial":0.9,"min":0.0,"max":1.5}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    stock = 0.0
    risk = 0.0
    pipe = 0.0
    for i in range(len(age)):
        remaining_life = i + 1.0
        exposure = 1.0 / (1.0 + (remaining_life / H) ** P)
        stock = stock + age[i]
        risk = risk + exposure * age[i]
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    q = S - stock - WP * pipe + A * risk
    return max(0.0, min(C, q))
