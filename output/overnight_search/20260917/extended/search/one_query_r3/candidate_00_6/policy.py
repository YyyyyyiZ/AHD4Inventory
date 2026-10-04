def compute_order_amount(age, pipeline, mu, cv, f, L):
    ST = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    SF = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":50.0}
    C = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":50.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":5.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    WF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    stock = 0.0
    fresh_stock = 0.0
    pipe = 0.0
    for i in range(m):
        freshness = (i + 1.0) / m
        stock = stock + age[i]
        fresh_stock = fresh_stock + age[i] * (freshness ** A)
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    total_trigger = ST - stock - WP * pipe
    fresh_trigger = SF - fresh_stock - WF * pipe
    q = max(total_trigger, fresh_trigger)
    return max(0.0, min(C, q))
