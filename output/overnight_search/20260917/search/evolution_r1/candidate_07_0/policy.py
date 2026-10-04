def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":8.0}
    T = 0.05 # OPT_PARAM: {"type":"float","initial":0.05,"min":0.0,"max":0.8}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    B = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.0}
    H = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}
    U = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":1.0}

    m = len(age)
    scenario_count = 16
    raw_effective = 0.0
    pipeline_stock = 0.0

    for i in range(m):
        stock = max(0.0, age[i])
        relative_life = (i + 1.0) / max(1.0, float(m))
        life_weight = T + (1.0 - T) * (relative_life ** A)
        raw_effective = raw_effective + stock * life_weight

    for j in range(len(pipeline)):
        pipeline_stock = pipeline_stock + max(0.0, pipeline[j])

    raw_effective = raw_effective + P * pipeline_stock

    r1_values = [0.0, 0.0]
    r2_values = [0.0, 0.0]
    mixture_weights = [0.0, 0.0]
    active_values = [0.0, 0.0]

    for stream in range(2):
        if stream == 0:
            g = max(0.0, min(1.0, f))
        else:
            g = 1.0 - max(0.0, min(1.0, f))

        M = g * mu
        if M > 0.0:
            V = g * (mu * cv) * (mu * cv)
            shape = V / (M * M) - 1.0 / M
            shape = max(1.0, shape)
            root = max(0.0, shape * shape - 1.0) ** 0.5
            b = 1.0 + shape + root
            c = 1.0 + shape - root
            mixture_weights[stream] = 1.0 / b
            r1_values[stream] = 1.0 - 2.0 / (2.0 + M * b)
            r2_values[stream] = 1.0 - 2.0 / (2.0 + M * c)
            active_values[stream] = 1.0

    permutations = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [5, 12, 1, 9, 3, 14, 7, 10, 0, 15, 6, 2, 13, 8, 11, 4],
        [10, 2, 14, 5, 8, 0, 12, 7, 15, 3, 11, 6, 1, 13, 4, 9],
        [1, 7, 13, 4, 15, 10, 2, 12, 6, 9, 0, 14, 8, 3, 5, 11]
    ]

    quantiles = [[0.0] * scenario_count for stream in range(2)]

    for stream in range(2):
        if active_values[stream] > 0.0:
            weight1 = mixture_weights[stream]
            r1 = r1_values[stream]
            r2 = r2_values[stream]

            for k in range(scenario_count):
                u = (k + 0.5) / scenario_count
                demand_value = 240.0

                for d in range(241):
                    tail = weight1 * (r1 ** (d + 1))
                    tail = tail + (1.0 - weight1) * (r2 ** (d + 1))
                    if 1.0 - tail >= u:
                        demand_value = float(d)
                        break

                quantiles[stream][k] = demand_value

    projected_values = [0.0] * scenario_count
    projected_mean = 0.0

    for s in range(scenario_count):
        projected = [0.0] * m

        for i in range(m):
            projected[i] = max(0.0, age[i])

        for step in range(L):
            fifo_index = permutations[(2 * step) % 4][s]
            lifo_index = permutations[(2 * step + 1) % 4][s]
            fifo_demand = quantiles[0][fifo_index]
            lifo_demand = quantiles[1][lifo_index]

            remaining = fifo_demand
            for i in range(m):
                take = min(projected[i], remaining)
                projected[i] = projected[i] - take
                remaining = remaining - take

            remaining = lifo_demand
            for i in range(m - 1, -1, -1):
                take = min(projected[i], remaining)
                projected[i] = projected[i] - take
                remaining = remaining - take

            shifted = [0.0] * m
            for i in range(m - 1):
                shifted[i] = projected[i + 1]

            if step < len(pipeline):
                shifted[m - 1] = max(0.0, pipeline[step])

            projected = shifted

        projected_effective = 0.0
        for i in range(m):
            relative_life = (i + 1.0) / max(1.0, float(m))
            life_weight = T + (1.0 - T) * (relative_life ** A)
            projected_effective = projected_effective + projected[i] * life_weight

        projected_values[s] = projected_effective
        projected_mean = projected_mean + projected_effective

    projected_mean = projected_mean / scenario_count
    central_effective = (1.0 - B) * raw_effective + B * projected_mean
    central_gap = max(0.0, S - central_effective)

    scenario_gaps = [0.0] * scenario_count
    mean_gap = 0.0

    for s in range(scenario_count):
        scenario_effective = (1.0 - B) * raw_effective + B * projected_values[s]
        scenario_gap = max(0.0, S - scenario_effective)
        scenario_gaps[s] = scenario_gap
        mean_gap = mean_gap + scenario_gap

    mean_gap = mean_gap / scenario_count

    for i in range(scenario_count - 1):
        for j in range(i + 1, scenario_count):
            if scenario_gaps[j] < scenario_gaps[i]:
                temporary = scenario_gaps[i]
                scenario_gaps[i] = scenario_gaps[j]
                scenario_gaps[j] = temporary

    median_gap = 0.5 * (scenario_gaps[7] + scenario_gaps[8])
    stochastic_gap = (1.0 - U) * mean_gap + U * median_gap
    gap = (1.0 - H) * central_gap + H * stochastic_gap
    order = max(0.0, min(C, gap))

    if order != order or order > 1.0e100:
        return 0.0
    return order
