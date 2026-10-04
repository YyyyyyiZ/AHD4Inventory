def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    C = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    W0 = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":3.0}
    W1 = 0.47 # OPT_PARAM: {"type":"float","initial":0.47,"min":0.0,"max":3.0}
    W2 = 0.73 # OPT_PARAM: {"type":"float","initial":0.73,"min":0.0,"max":3.0}
    W3 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    m = len(age)
    effective = 0.0
    for i in range(m):
        if m > 1:
            x = float(i) / float(m - 1)
        else:
            x = 1.0
        u = 1.0 - x
        weight = W0*u*u*u + 3.0*W1*x*u*u + 3.0*W2*x*x*u + W3*x*x*x
        effective = effective + weight*age[i]
    pipe_stock = 0.0
    for j in range(len(pipeline)):
        pipe_stock = pipe_stock + pipeline[j]
    order = S - effective - P*pipe_stock
    if not (order >= 0.0):
        return 0.0
    if order > C:
        return C
    return order
