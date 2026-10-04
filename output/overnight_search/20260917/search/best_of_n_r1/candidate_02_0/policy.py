def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    projection_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    age_power = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":10.0}
    inventory_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}

    m = len(age)
    if m <= 0:
        return 0.0

    x = [0.0 for _ in range(m)]
    for i in range(m):
        value = float(age[i])
        if value < 0.0 or value != value:
            value = 0.0
        x[i] = value

    mf = f * mu
    ml = (1.0 - f) * mu
    demand_sd = mu * cv

    rf1 = 0.0
    rf2 = 0.0
    wf1 = 0.0
    if mf > 0.0:
        vf = f * demand_sd * demand_sd
        af = vf / (mf * mf) - 1.0 / mf
        if af < 1.0:
            af = 1.0
        rootf = (af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf1 = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    rl1 = 0.0
    rl2 = 0.0
    wl1 = 0.0
    if ml > 0.0:
        vl = (1.0 - f) * demand_sd * demand_sd
        al = vl / (ml * ml) - 1.0 / ml
        if al < 1.0:
            al = 1.0
        rootl = (al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl1 = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    lead = int(L)
    if lead < 0:
        lead = 0

    for t in range(lead):
        if mf > 0.0:
            rank = 0.0
            for i in range(m):
                amount = x[i]
                if amount > 0.0:
                    part1 = wf1 * (rf1 ** (rank + 1.0)) * (1.0 - rf1 ** amount) / (1.0 - rf1)
                    part2 = (1.0 - wf1) * (rf2 ** (rank + 1.0)) * (1.0 - rf2 ** amount) / (1.0 - rf2)
                    consumed = projection_scale * (part1 + part2)
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > amount:
                        consumed = amount
                    x[i] = amount - consumed
                    rank = rank + amount

        if ml > 0.0:
            rank = 0.0
            for k in range(m):
                i = m - 1 - k
                amount = x[i]
                if amount > 0.0:
                    part1 = wl1 * (rl1 ** (rank + 1.0)) * (1.0 - rl1 ** amount) / (1.0 - rl1)
                    part2 = (1.0 - wl1) * (rl2 ** (rank + 1.0)) * (1.0 - rl2 ** amount) / (1.0 - rl2)
                    consumed = projection_scale * (part1 + part2)
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > amount:
                        consumed = amount
                    x[i] = amount - consumed
                    rank = rank + amount

        shifted = [0.0 for _ in range(m)]
        for i in range(m - 1):
            shifted[i] = x[i + 1]

        incoming = 0.0
        if t < len(pipeline):
            incoming = float(pipeline[t])
            if incoming < 0.0 or incoming != incoming:
                incoming = 0.0
        shifted[m - 1] = incoming
        x = shifted

    effective_inventory = 0.0
    for i in range(m):
        remaining_fraction = float(i + 1) / float(m)
        weight = remaining_fraction ** age_power
        effective_inventory = effective_inventory + weight * x[i]

    order = S - inventory_credit * effective_inventory
    if order != order or order <= 0.0:
        return 0.0
    if order > 1000000.0:
        return 1000000.0
    return float(order)
