def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    lead_sales_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    carry_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    stale_weight = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-2.0,"max":4.0}
    stale_power = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":5.0}
    reaction = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.0}

    m = len(age)
    x = [0.0 for _ in range(m)]
    for i in range(m):
        v = float(age[i])
        if v < 0.0:
            v = 0.0
        x[i] = v

    mean_f = f * mu
    mean_l = (1.0 - f) * mu
    total_variance = (mu * cv) * (mu * cv)

    active_f = mean_f > 0.0
    if active_f:
        var_f = f * total_variance
        a_f = var_f / (mean_f * mean_f) - 1.0 / mean_f
        root_f = (max(0.0, a_f * a_f - 1.0)) ** 0.5
        b_f = 1.0 + a_f + root_f
        c_f = 1.0 + a_f - root_f
        mix_f = 1.0 / b_f
        p1_f = 2.0 / (2.0 + mean_f * b_f)
        p2_f = 2.0 / (2.0 + mean_f * c_f)
        r1_f = 1.0 - p1_f
        r2_f = 1.0 - p2_f
        e1_f = r1_f / p1_f
        e2_f = r2_f / p2_f
    else:
        mix_f = 0.0
        p1_f = 1.0
        p2_f = 1.0
        r1_f = 0.0
        r2_f = 0.0
        e1_f = 0.0
        e2_f = 0.0

    active_l = mean_l > 0.0
    if active_l:
        var_l = (1.0 - f) * total_variance
        a_l = var_l / (mean_l * mean_l) - 1.0 / mean_l
        root_l = (max(0.0, a_l * a_l - 1.0)) ** 0.5
        b_l = 1.0 + a_l + root_l
        c_l = 1.0 + a_l - root_l
        mix_l = 1.0 / b_l
        p1_l = 2.0 / (2.0 + mean_l * b_l)
        p2_l = 2.0 / (2.0 + mean_l * c_l)
        r1_l = 1.0 - p1_l
        r2_l = 1.0 - p2_l
        e1_l = r1_l / p1_l
        e2_l = r2_l / p2_l
    else:
        mix_l = 0.0
        p1_l = 1.0
        p2_l = 1.0
        r1_l = 0.0
        r2_l = 0.0
        e1_l = 0.0
        e2_l = 0.0

    lead = int(L)
    if lead < 0:
        lead = 0

    for step in range(lead):
        if active_f:
            cumulative = 0.0
            for i in range(m):
                stock = x[i]
                if stock > 0.0:
                    before = mix_f * e1_f * (r1_f ** cumulative) + (1.0 - mix_f) * e2_f * (r2_f ** cumulative)
                    after_point = cumulative + stock
                    after = mix_f * e1_f * (r1_f ** after_point) + (1.0 - mix_f) * e2_f * (r2_f ** after_point)
                    used = lead_sales_scale * (before - after)
                    if used < 0.0:
                        used = 0.0
                    if used > stock:
                        used = stock
                    x[i] = stock - used
                    cumulative = cumulative + stock

        if active_l:
            cumulative = 0.0
            for k in range(m):
                i = m - 1 - k
                stock = x[i]
                if stock > 0.0:
                    before = mix_l * e1_l * (r1_l ** cumulative) + (1.0 - mix_l) * e2_l * (r2_l ** cumulative)
                    after_point = cumulative + stock
                    after = mix_l * e1_l * (r1_l ** after_point) + (1.0 - mix_l) * e2_l * (r2_l ** after_point)
                    used = lead_sales_scale * (before - after)
                    if used < 0.0:
                        used = 0.0
                    if used > stock:
                        used = stock
                    x[i] = stock - used
                    cumulative = cumulative + stock

        for i in range(m - 1):
            x[i] = x[i + 1]

        arrival = 0.0
        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival < 0.0:
                arrival = 0.0
        if m > 0:
            x[m - 1] = arrival

    effective_carry = 0.0
    if m > 0:
        denominator = float(max(1, m - 1))
        for i in range(m):
            staleness = float(m - 1 - i) / denominator
            weight = carry_weight + stale_weight * (staleness ** stale_power)
            if weight < 0.0:
                weight = 0.0
            if weight > 6.0:
                weight = 6.0
            effective_carry = effective_carry + weight * x[i]

    deficit = S - effective_carry
    if deficit <= 0.0:
        return 0.0

    order = reaction * deficit
    if not (order >= 0.0):
        return 0.0
    if order > 120.0:
        order = 120.0
    return order
