def compute_order_amount(age, pipeline, mu, cv, f, L):
    TARGET = 15.0 # OPT_PARAM: {"type":"float","initial":15.0,"min":0.0,"max":60.0}
    MAX_ORDER = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    POS_SCALE = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.2,"max":2.0}
    AGE_POWER = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":5.0}
    CARRY_RISK = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":2.0}

    m = len(age)
    if m == 0:
        return 0.0

    base_variance = (mu * cv) * (mu * cv)

    mean_fifo = f * mu
    var_fifo = f * base_variance
    if mean_fifo > 0.0:
        af = var_fifo / (mean_fifo * mean_fifo) - 1.0 / mean_fifo
        if af < 1.0:
            af = 1.0
        rootf = (af * af - 1.0) ** 0.5
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        weightf = 1.0 / bf
        prob1f = 2.0 / (2.0 + mean_fifo * bf)
        prob2f = 2.0 / (2.0 + mean_fifo * cf)
        zero_fifo = weightf * prob1f + (1.0 - weightf) * prob2f
        pos_fifo = max(0.0, min(1.0, 1.0 - zero_fifo))
        cond_fifo = mean_fifo / pos_fifo if pos_fifo > 1.0e-12 else 0.0
    else:
        pos_fifo = 0.0
        cond_fifo = 0.0

    mean_lifo = (1.0 - f) * mu
    var_lifo = (1.0 - f) * base_variance
    if mean_lifo > 0.0:
        al = var_lifo / (mean_lifo * mean_lifo) - 1.0 / mean_lifo
        if al < 1.0:
            al = 1.0
        rootl = (al * al - 1.0) ** 0.5
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        weightl = 1.0 / bl
        prob1l = 2.0 / (2.0 + mean_lifo * bl)
        prob2l = 2.0 / (2.0 + mean_lifo * cl)
        zero_lifo = weightl * prob1l + (1.0 - weightl) * prob2l
        pos_lifo = max(0.0, min(1.0, 1.0 - zero_lifo))
        cond_lifo = mean_lifo / pos_lifo if pos_lifo > 1.0e-12 else 0.0
    else:
        pos_lifo = 0.0
        cond_lifo = 0.0

    exponent = AGE_POWER * (0.05 + 1.9 * f)
    age_weight = [0.0] * m
    for i in range(m):
        age_weight[i] = ((i + 1.0) / m) ** exponent

    scenario_count = 1 << (2 * L)
    probability_sum = 0.0
    effective_mean = 0.0
    effective_second = 0.0

    for mask in range(scenario_count):
        probability = 1.0
        for t in range(L):
            fifo_positive = ((mask >> (2 * t)) & 1) == 1
            lifo_positive = ((mask >> (2 * t + 1)) & 1) == 1
            if fifo_positive:
                probability = probability * pos_fifo
            else:
                probability = probability * (1.0 - pos_fifo)
            if lifo_positive:
                probability = probability * pos_lifo
            else:
                probability = probability * (1.0 - pos_lifo)

        if probability > 1.0e-15:
            stock = [0.0] * m
            for i in range(m):
                stock[i] = float(age[i])

            for t in range(L):
                if t > 0 and t - 1 < len(pipeline):
                    stock[m - 1] = stock[m - 1] + float(pipeline[t - 1])

                fifo_positive = ((mask >> (2 * t)) & 1) == 1
                lifo_positive = ((mask >> (2 * t + 1)) & 1) == 1
                fifo_demand = cond_fifo * POS_SCALE if fifo_positive else 0.0
                lifo_demand = cond_lifo * POS_SCALE if lifo_positive else 0.0

                remaining = fifo_demand
                if remaining > 0.0:
                    for i in range(m):
                        take = min(stock[i], remaining)
                        stock[i] = stock[i] - take
                        remaining = remaining - take

                remaining = lifo_demand
                if remaining > 0.0:
                    for k in range(m):
                        i = m - 1 - k
                        take = min(stock[i], remaining)
                        stock[i] = stock[i] - take
                        remaining = remaining - take

                for i in range(m - 1):
                    stock[i] = stock[i + 1]
                stock[m - 1] = 0.0

            effective = 0.0
            for i in range(m):
                effective = effective + age_weight[i] * stock[i]

            probability_sum = probability_sum + probability
            effective_mean = effective_mean + probability * effective
            effective_second = effective_second + probability * effective * effective

    if probability_sum > 0.0:
        effective_mean = effective_mean / probability_sum
        effective_second = effective_second / probability_sum

    effective_variance = effective_second - effective_mean * effective_mean
    if effective_variance < 0.0:
        effective_variance = 0.0
    effective_std = effective_variance ** 0.5
    effective_carry = effective_mean + CARRY_RISK * effective_std

    order = TARGET - effective_carry
    if order <= 0.0:
        return 0.0
    if order > MAX_ORDER:
        return float(MAX_ORDER)
    return float(order)
