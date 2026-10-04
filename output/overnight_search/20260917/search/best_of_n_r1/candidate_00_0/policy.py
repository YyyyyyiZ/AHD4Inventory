def compute_order_amount(age, pipeline, mu, cv, f, L):
    Q_MULT = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":6.0}
    LEAD_DEMAND_SCALE = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":1.5}
    PROJECTED_CREDIT = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    RISK_CREDIT = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.5}
    FIFO_FLOOR = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.0}
    LIFO_FLOOR = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.0,"max":1.0}
    LIFO_AGE_POWER = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.2,"max":8.0}

    m = len(age)
    if m <= 0:
        return 0.0

    lead = int(L)
    if lead < 0:
        lead = 0

    fifo_share = float(f)
    if fifo_share < 0.0:
        fifo_share = 0.0
    if fifo_share > 1.0:
        fifo_share = 1.0

    work = [0.0] * m
    no_demand_work = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value < 0.0 or value != value:
            value = 0.0
        work[i] = value
        no_demand_work[i] = value

    fifo_demand = LEAD_DEMAND_SCALE * fifo_share * float(mu)
    lifo_demand = LEAD_DEMAND_SCALE * (1.0 - fifo_share) * float(mu)

    for t in range(lead):
        remaining = fifo_demand
        for i in range(m):
            available = work[i]
            if available <= remaining:
                work[i] = 0.0
                remaining = remaining - available
            else:
                work[i] = available - remaining
                remaining = 0.0

        remaining = lifo_demand
        for i in range(m - 1, -1, -1):
            available = work[i]
            if available <= remaining:
                work[i] = 0.0
                remaining = remaining - available
            else:
                work[i] = available - remaining
                remaining = 0.0

        shifted = [0.0] * m
        no_demand_shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = work[i + 1]
            no_demand_shifted[i] = no_demand_work[i + 1]

        if t < lead - 1 and t < len(pipeline):
            arrival = float(pipeline[t])
            if arrival < 0.0 or arrival != arrival:
                arrival = 0.0
            shifted[m - 1] = arrival
            no_demand_shifted[m - 1] = arrival

        work = shifted
        no_demand_work = no_demand_shifted

    projected_credit = 0.0
    no_demand_credit = 0.0
    for i in range(m):
        relative_life = float(i + 1) / float(m)
        fifo_utility = FIFO_FLOOR + (1.0 - FIFO_FLOOR) * relative_life
        lifo_utility = LIFO_FLOOR + (1.0 - LIFO_FLOOR) * (relative_life ** LIFO_AGE_POWER)
        utility = fifo_share * fifo_utility + (1.0 - fifo_share) * lifo_utility
        projected_credit = projected_credit + utility * work[i]
        no_demand_credit = no_demand_credit + utility * no_demand_work[i]

    uncertain_credit = no_demand_credit - projected_credit
    if uncertain_credit < 0.0:
        uncertain_credit = 0.0

    raw_order = (
        Q_MULT * float(mu)
        - PROJECTED_CREDIT * projected_credit
        - RISK_CREDIT * uncertain_credit
    )

    if raw_order != raw_order or raw_order < 0.0:
        raw_order = 0.0
    if raw_order > 1000000.0:
        raw_order = 1000000.0

    return float(raw_order)
