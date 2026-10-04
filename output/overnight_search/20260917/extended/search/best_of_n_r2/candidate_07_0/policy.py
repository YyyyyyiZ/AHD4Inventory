def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 9.0 # OPT_PARAM: {"type":"float","initial":9.0,"min":0.0,"max":60.0}
    C = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    age_floor = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.0}
    age_power = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":4.0}
    projection_blend = 0.7 # OPT_PARAM: {"type":"float","initial":0.7,"min":0.0,"max":1.0}
    fifo_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    lifo_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    mixture_spread = 1.7 # OPT_PARAM: {"type":"float","initial":1.7,"min":0.0,"max":2.5}
    projection_risk = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-1.5,"max":2.5}

    m = len(age)
    raw_effective = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        weight = age_floor + (1.0 - age_floor) * (x ** age_power)
        raw_effective = raw_effective + age[i] * weight
    for j in range(len(pipeline)):
        raw_effective = raw_effective + pipeline[j]

    fifo_mean = f * mu
    lifo_mean = (1.0 - f) * mu
    fifo_demand = [0.0, 0.0]
    lifo_demand = [0.0, 0.0]
    fifo_prob = [1.0, 0.0]
    lifo_prob = [1.0, 0.0]

    if fifo_mean > 0.0:
        fifo_var = f * (mu * cv) * (mu * cv)
        shape = fifo_var / (fifo_mean * fifo_mean) - 1.0 / fifo_mean
        root = max(0.0, shape * shape - 1.0) ** 0.5
        b = 1.0 + shape + root
        c = 1.0 + shape - root
        fifo_prob[0] = 1.0 / b
        fifo_prob[1] = 1.0 - fifo_prob[0]
        component_high = fifo_mean * b * 0.5
        component_low = fifo_mean * c * 0.5
        fifo_demand[0] = fifo_scale * max(0.0, fifo_mean + mixture_spread * (component_high - fifo_mean))
        fifo_demand[1] = fifo_scale * max(0.0, fifo_mean + mixture_spread * (component_low - fifo_mean))

    if lifo_mean > 0.0:
        lifo_var = (1.0 - f) * (mu * cv) * (mu * cv)
        shape = lifo_var / (lifo_mean * lifo_mean) - 1.0 / lifo_mean
        root = max(0.0, shape * shape - 1.0) ** 0.5
        b = 1.0 + shape + root
        c = 1.0 + shape - root
        lifo_prob[0] = 1.0 / b
        lifo_prob[1] = 1.0 - lifo_prob[0]
        component_high = lifo_mean * b * 0.5
        component_low = lifo_mean * c * 0.5
        lifo_demand[0] = lifo_scale * max(0.0, lifo_mean + mixture_spread * (component_high - lifo_mean))
        lifo_demand[1] = lifo_scale * max(0.0, lifo_mean + mixture_spread * (component_low - lifo_mean))

    expected_effective = 0.0
    expected_square = 0.0
    total_probability = 0.0

    for path in range(16):
        fifo_first = path % 2
        lifo_first = (path // 2) % 2
        fifo_second = (path // 4) % 2
        lifo_second = (path // 8) % 2
        probability = fifo_prob[fifo_first] * lifo_prob[lifo_first]
        probability = probability * fifo_prob[fifo_second] * lifo_prob[lifo_second]

        if probability > 0.0:
            stock = [0.0] * m
            for i in range(m):
                stock[i] = max(0.0, age[i])

            for period in range(2):
                if period == 1 and len(pipeline) > 0:
                    stock[m - 1] = stock[m - 1] + max(0.0, pipeline[0])

                if period == 0:
                    fifo_remaining = fifo_demand[fifo_first]
                    lifo_remaining = lifo_demand[lifo_first]
                else:
                    fifo_remaining = fifo_demand[fifo_second]
                    lifo_remaining = lifo_demand[lifo_second]

                for i in range(m):
                    served = min(stock[i], fifo_remaining)
                    stock[i] = stock[i] - served
                    fifo_remaining = fifo_remaining - served

                for k in range(m):
                    i = m - 1 - k
                    served = min(stock[i], lifo_remaining)
                    stock[i] = stock[i] - served
                    lifo_remaining = lifo_remaining - served

                for i in range(m - 1):
                    stock[i] = stock[i + 1]
                stock[m - 1] = 0.0

            scenario_effective = 0.0
            for i in range(m):
                x = (i + 1.0) / m
                weight = age_floor + (1.0 - age_floor) * (x ** age_power)
                scenario_effective = scenario_effective + stock[i] * weight

            expected_effective = expected_effective + probability * scenario_effective
            expected_square = expected_square + probability * scenario_effective * scenario_effective
            total_probability = total_probability + probability

    if total_probability > 0.0:
        expected_effective = expected_effective / total_probability
        expected_square = expected_square / total_probability

    variance_effective = max(0.0, expected_square - expected_effective * expected_effective)
    projected_effective = expected_effective - projection_risk * (variance_effective ** 0.5)
    control_inventory = projection_blend * projected_effective
    control_inventory = control_inventory + (1.0 - projection_blend) * raw_effective
    order = S - control_inventory
    return max(0.0, min(C, order))
