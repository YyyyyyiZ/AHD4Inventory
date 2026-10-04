def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 22.0 # OPT_PARAM: {"type":"float","initial":22.0,"min":0.0,"max":60.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.5,"max":1.5}
    burst_mix = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.0}
    life_floor = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}
    life_power = 1.4 # OPT_PARAM: {"type":"float","initial":1.4,"min":0.1,"max":6.0}
    fifo_age_boost = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    credit_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    uncertainty_adjust = -0.25 # OPT_PARAM: {"type":"float","initial":-0.25,"min":-2.0,"max":2.0}

    m = len(age)
    means = [f * mu, (1.0 - f) * mu]
    total_variance = (mu * cv) * (mu * cv)
    variances = [f * total_variance, (1.0 - f) * total_variance]
    event_rates = [0.0, 0.0]
    event_amounts = [0.0, 0.0]

    for s in range(2):
        M = means[s]
        V = variances[s]
        if M > 0.0:
            a = V / (M * M) - 1.0 / M
            root = (a * a - 1.0) ** 0.5
            b = 1.0 + a + root
            c = 1.0 + a - root
            mixture_weight = 1.0 / b
            success1 = 2.0 / (2.0 + M * b)
            success2 = 2.0 / (2.0 + M * c)
            probability_zero = mixture_weight * success1 + (1.0 - mixture_weight) * success2
            actual_event_rate = 1.0 - probability_zero
            moment_event_rate = (M * M) / (V + M * M)
            event_rate = (1.0 - burst_mix) * actual_event_rate + burst_mix * moment_event_rate
            if event_rate < 0.000001:
                event_rate = 0.000001
            if event_rate > 0.999999:
                event_rate = 0.999999
            event_rates[s] = event_rate
            event_amounts[s] = demand_scale * M / event_rate

    scenario_count = 2 ** (2 * L)
    first_moment = 0.0
    second_moment = 0.0

    for mask in range(scenario_count):
        scenario_weight = 1.0
        x = [0.0] * m
        for i in range(m):
            x[i] = float(age[i])

        for t in range(L):
            fifo_bit = (mask // (2 ** (2 * t))) % 2
            lifo_bit = (mask // (2 ** (2 * t + 1))) % 2

            if fifo_bit == 1:
                scenario_weight = scenario_weight * event_rates[0]
                fifo_demand = event_amounts[0]
            else:
                scenario_weight = scenario_weight * (1.0 - event_rates[0])
                fifo_demand = 0.0

            if lifo_bit == 1:
                scenario_weight = scenario_weight * event_rates[1]
                lifo_demand = event_amounts[1]
            else:
                scenario_weight = scenario_weight * (1.0 - event_rates[1])
                lifo_demand = 0.0

            remaining = fifo_demand
            for i in range(m):
                if remaining > 0.0:
                    if x[i] <= remaining:
                        remaining = remaining - x[i]
                        x[i] = 0.0
                    else:
                        x[i] = x[i] - remaining
                        remaining = 0.0

            remaining = lifo_demand
            for k in range(m):
                i = m - 1 - k
                if remaining > 0.0:
                    if x[i] <= remaining:
                        remaining = remaining - x[i]
                        x[i] = 0.0
                    else:
                        x[i] = x[i] - remaining
                        remaining = 0.0

            x[0] = 0.0
            for i in range(m - 1):
                x[i] = x[i + 1]
            x[m - 1] = 0.0

            if t < L - 1 and t < len(pipeline):
                x[m - 1] = x[m - 1] + float(pipeline[t])

        effective_inventory = 0.0
        for i in range(m):
            relative_life = float(i + 1) / float(m)
            relative_life = relative_life + fifo_age_boost * f * (1.0 - relative_life)
            if relative_life < 0.0:
                relative_life = 0.0
            if relative_life > 1.0:
                relative_life = 1.0
            age_credit = life_floor + (1.0 - life_floor) * (relative_life ** life_power)
            effective_inventory = effective_inventory + age_credit * x[i]

        first_moment = first_moment + scenario_weight * effective_inventory
        second_moment = second_moment + scenario_weight * effective_inventory * effective_inventory

    projected_variance = second_moment - first_moment * first_moment
    if projected_variance < 0.0:
        projected_variance = 0.0
    projected_deviation = projected_variance ** 0.5
    inventory_credit = credit_scale * (first_moment + uncertainty_adjust * projected_deviation)
    if inventory_credit < 0.0:
        inventory_credit = 0.0

    order_amount = S - inventory_credit
    if not (order_amount >= 0.0):
        order_amount = 0.0
    if order_amount > 1000000.0:
        order_amount = 1000000.0
    return float(order_amount)
