def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 14.5 # OPT_PARAM: {"type":"float","initial":14.5,"min":0.0,"max":60.0}
    C = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    G = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":3.0}
    Q = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-0.1,"max":0.1}
    KF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":1.75}
    KL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":1.75}
    W0 = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":0.0,"max":1.0}
    A = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.01,"max":4.0}
    B = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-0.9,"max":3.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    R = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.0}

    m = len(age)
    if m <= 0:
        return 0.0

    power = A + 1.8*f
    static_effective = 0.0
    for i in range(m):
        z = (i + 1.0)/m
        core = (z**power)*(1.0 + B*(1.0 - z))
        if core < 0.0:
            core = 0.0
        weight = W0 + (1.0 - W0)*core
        units = age[i]
        if units < 0.0:
            units = 0.0
        static_effective = static_effective + weight*units

    pipeline_total = 0.0
    for j in range(len(pipeline)):
        units = pipeline[j]
        if units > 0.0:
            pipeline_total = pipeline_total + units
    static_effective = static_effective + WP*pipeline_total

    x = [0.0 for i in range(m)]
    for i in range(m):
        units = age[i]
        if units < 0.0:
            units = 0.0
        x[i] = units

    mf = f*mu
    vf = f*(mu*cv)*(mu*cv)
    ml = (1.0 - f)*mu
    vl = (1.0 - f)*(mu*cv)*(mu*cv)

    wf1 = 0.0
    pf1 = 1.0
    pf2 = 1.0
    rf1 = 0.0
    rf2 = 0.0
    if mf > 0.0:
        af = vf/(mf*mf) - 1.0/mf
        if af < 1.0:
            af = 1.0
        discf = af*af - 1.0
        if discf < 0.0:
            discf = 0.0
        bf = 1.0 + af + discf**0.5
        cf = 1.0 + af - discf**0.5
        wf1 = 1.0/bf
        pf1 = 2.0/(2.0 + mf*bf)
        pf2 = 2.0/(2.0 + mf*cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    wl1 = 0.0
    pl1 = 1.0
    pl2 = 1.0
    rl1 = 0.0
    rl2 = 0.0
    if ml > 0.0:
        al = vl/(ml*ml) - 1.0/ml
        if al < 1.0:
            al = 1.0
        discl = al*al - 1.0
        if discl < 0.0:
            discl = 0.0
        bl = 1.0 + al + discl**0.5
        cl = 1.0 + al - discl**0.5
        wl1 = 1.0/bl
        pl1 = 2.0/(2.0 + ml*bl)
        pl2 = 2.0/(2.0 + ml*cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    for t in range(L):
        stock = 0.0
        for i in range(m):
            stock = stock + x[i]

        fifo_sales = 0.0
        if mf > 0.0 and stock > 0.0:
            fifo_sales = wf1*rf1*(1.0 - rf1**stock)/pf1
            fifo_sales = fifo_sales + (1.0 - wf1)*rf2*(1.0 - rf2**stock)/pf2
            fifo_sales = KF*fifo_sales
            if fifo_sales > stock:
                fifo_sales = stock
            if fifo_sales < 0.0:
                fifo_sales = 0.0

        remaining = fifo_sales
        for i in range(m):
            take = remaining
            if take > x[i]:
                take = x[i]
            if take < 0.0:
                take = 0.0
            x[i] = x[i] - take
            remaining = remaining - take

        stock = 0.0
        for i in range(m):
            stock = stock + x[i]

        lifo_sales = 0.0
        if ml > 0.0 and stock > 0.0:
            lifo_sales = wl1*rl1*(1.0 - rl1**stock)/pl1
            lifo_sales = lifo_sales + (1.0 - wl1)*rl2*(1.0 - rl2**stock)/pl2
            lifo_sales = KL*lifo_sales
            if lifo_sales > stock:
                lifo_sales = stock
            if lifo_sales < 0.0:
                lifo_sales = 0.0

        remaining = lifo_sales
        for k in range(m):
            i = m - 1 - k
            take = remaining
            if take > x[i]:
                take = x[i]
            if take < 0.0:
                take = 0.0
            x[i] = x[i] - take
            remaining = remaining - take

        for i in range(m - 1):
            x[i] = x[i + 1]
        x[m - 1] = 0.0

        if t < len(pipeline):
            arrival = pipeline[t]
            if arrival > 0.0:
                x[m - 1] = x[m - 1] + arrival

    projected_effective = 0.0
    for i in range(m):
        z = (i + 1.0)/m
        core = (z**power)*(1.0 + B*(1.0 - z))
        if core < 0.0:
            core = 0.0
        weight = W0 + (1.0 - W0)*core
        projected_effective = projected_effective + weight*x[i]

    effective = R*projected_effective + (1.0 - R)*static_effective
    gap = S - effective
    gain = G + Q*gap
    if gain < 0.0:
        gain = 0.0
    if gain > 3.0:
        gain = 3.0

    order = gain*gap
    if order < 0.0:
        order = 0.0
    if order > C:
        order = C
    if order != order:
        order = 0.0
    return float(order)
