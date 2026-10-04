def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 19.0 # OPT_PARAM: {"type":"float","initial":19.0,"min":0.0,"max":60.0}
    KF = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":3.0}
    KL = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":3.0}
    PS = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":1.5}
    C0 = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.5}
    CS = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":-0.5,"max":1.5}

    m = len(age)
    x0 = float(age[0]) if m > 0 else 0.0
    x1 = float(age[1]) if m > 1 else 0.0
    x2 = float(age[2]) if m > 2 else 0.0
    x3 = float(age[3]) if m > 3 else 0.0
    x4 = float(age[4]) if m > 4 else 0.0

    steps = int(L)
    if steps < 0:
        steps = 0
    if steps > 8:
        steps = 8

    for step in range(steps):
        demand_fifo = KF * f * mu
        take = min(x0, demand_fifo)
        x0 = x0 - take
        demand_fifo = demand_fifo - take
        take = min(x1, demand_fifo)
        x1 = x1 - take
        demand_fifo = demand_fifo - take
        take = min(x2, demand_fifo)
        x2 = x2 - take
        demand_fifo = demand_fifo - take
        take = min(x3, demand_fifo)
        x3 = x3 - take
        demand_fifo = demand_fifo - take
        take = min(x4, demand_fifo)
        x4 = x4 - take

        demand_lifo = KL * (1.0 - f) * mu
        take = min(x4, demand_lifo)
        x4 = x4 - take
        demand_lifo = demand_lifo - take
        take = min(x3, demand_lifo)
        x3 = x3 - take
        demand_lifo = demand_lifo - take
        take = min(x2, demand_lifo)
        x2 = x2 - take
        demand_lifo = demand_lifo - take
        take = min(x1, demand_lifo)
        x1 = x1 - take
        demand_lifo = demand_lifo - take
        take = min(x0, demand_lifo)
        x0 = x0 - take

        arrival = 0.0
        if step < len(pipeline):
            arrival = PS * float(pipeline[step])

        if m == 3:
            x0 = x1
            x1 = x2
            x2 = arrival
            x3 = 0.0
            x4 = 0.0
        elif m == 4:
            x0 = x1
            x1 = x2
            x2 = x3
            x3 = arrival
            x4 = 0.0
        else:
            x0 = x1
            x1 = x2
            x2 = x3
            x3 = x4
            x4 = arrival

    denominator = float(max(1, m - 1))
    w0 = max(0.0, min(2.0, C0))
    w1 = max(0.0, min(2.0, C0 + CS / denominator))
    w2 = max(0.0, min(2.0, C0 + 2.0 * CS / denominator))
    w3 = max(0.0, min(2.0, C0 + 3.0 * CS / denominator))
    w4 = max(0.0, min(2.0, C0 + 4.0 * CS / denominator))

    projected_inventory = w0 * x0 + w1 * x1 + w2 * x2 + w3 * x3 + w4 * x4
    q = S - projected_inventory
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 120.0:
        q = 120.0
    return float(q)
