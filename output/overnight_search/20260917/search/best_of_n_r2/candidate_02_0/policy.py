def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    fifo_projection = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.0}
    lifo_projection = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.0}
    young_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    old_premium = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    age_power = 1.5 # OPT_PARAM: {"type":"float","initial":1.5,"min":0.25,"max":4.0}
    crowding = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":4.0}

    m = len(age)
    stock = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value < 0.0:
            value = 0.0
        stock[i] = value

    fifo_mean = f * mu
    lifo_share = 1.0 - f
    lifo_mean = lifo_share * mu
    demand_scale = mu * cv

    fifo_on = fifo_mean > 0.0
    if fifo_on:
        fifo_variance = f * demand_scale * demand_scale
        af = fifo_variance / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        if af < 1.0:
            af = 1.0
        rootf = (af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        mixf = 1.0 / bf
        pf1 = 2.0 / (2.0 + fifo_mean * bf)
        pf2 = 2.0 / (2.0 + fifo_mean * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    lifo_on = lifo_mean > 0.0
    if lifo_on:
        lifo_variance = lifo_share * demand_scale * demand_scale
        al = lifo_variance / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        if al < 1.0:
            al = 1.0
        rootl = (al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        mixl = 1.0 / bl
        pl1 = 2.0 / (2.0 + lifo_mean * bl)
        pl2 = 2.0 / (2.0 + lifo_mean * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    for step in range(L):
        if step > 0 and step - 1 < len(pipeline):
            arrival = float(pipeline[step - 1])
            if arrival > 0.0:
                stock[m - 1] = stock[m - 1] + arrival

        if fifo_on:
            cumulative = 0.0
            previous_expected = 0.0
            for i in range(m):
                amount = stock[i]
                cumulative = cumulative + amount
                whole = int(cumulative)
                fraction = cumulative - whole
                expected1 = rf1 * (1.0 - rf1 ** whole) / pf1
                expected1 = expected1 + fraction * rf1 ** (whole + 1)
                expected2 = rf2 * (1.0 - rf2 ** whole) / pf2
                expected2 = expected2 + fraction * rf2 ** (whole + 1)
                expected = mixf * expected1 + (1.0 - mixf) * expected2
                consumed = fifo_projection * (expected - previous_expected)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > amount:
                    consumed = amount
                stock[i] = amount - consumed
                previous_expected = expected

        if lifo_on:
            cumulative = 0.0
            previous_expected = 0.0
            for k in range(m):
                i = m - 1 - k
                amount = stock[i]
                cumulative = cumulative + amount
                whole = int(cumulative)
                fraction = cumulative - whole
                expected1 = rl1 * (1.0 - rl1 ** whole) / pl1
                expected1 = expected1 + fraction * rl1 ** (whole + 1)
                expected2 = rl2 * (1.0 - rl2 ** whole) / pl2
                expected2 = expected2 + fraction * rl2 ** (whole + 1)
                expected = mixl * expected1 + (1.0 - mixl) * expected2
                consumed = lifo_projection * (expected - previous_expected)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > amount:
                    consumed = amount
                stock[i] = amount - consumed
                previous_expected = expected

        for i in range(m - 1):
            stock[i] = stock[i + 1]
        stock[m - 1] = 0.0

    effective_stock = 0.0
    age_risk = 0.0
    denominator = float(max(1, m - 1))
    for i in range(m):
        oldness = float(m - 1 - i) / denominator
        risk_shape = oldness ** age_power
        weight = young_weight + old_premium * lifo_share * risk_shape
        effective_stock = effective_stock + weight * stock[i]
        age_risk = age_risk + risk_shape * stock[i]

    congestion_denominator = mu + age_risk + 1.0e-12
    effective_stock = effective_stock + crowding * lifo_share * age_risk * age_risk / congestion_denominator

    order = S - effective_stock
    if order < 0.0:
        order = 0.0
    if order > 60.0:
        order = 60.0
    return float(order)
