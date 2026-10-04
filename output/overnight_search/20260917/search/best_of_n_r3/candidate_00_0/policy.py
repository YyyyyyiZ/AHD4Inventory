def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    Q = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":60.0}
    fifo_depletion = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.0}
    lifo_depletion = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.0}
    old_weight = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":2.5}
    young_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}

    m = len(age)
    lead = int(L)
    x = [float(age[i]) for i in range(m)]

    groups = [float(f), 1.0 - float(f)]
    means = [groups[0] * float(mu), groups[1] * float(mu)]
    demand_variance = (float(mu) * float(cv)) * (float(mu) * float(cv))
    variances = [groups[0] * demand_variance, groups[1] * demand_variance]

    probabilities = [[1.0, 1.0], [1.0, 1.0]]
    weights = [[1.0, 0.0], [1.0, 0.0]]

    for stream in range(2):
        M = means[stream]
        if M > 0.0:
            V = variances[stream]
            a = V / (M * M) - 1.0 / M
            discriminant = a * a - 1.0
            if discriminant < 0.0:
                discriminant = 0.0
            root = discriminant ** 0.5
            b = 1.0 + a + root
            c = 1.0 + a - root
            w1 = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            probabilities[stream][0] = p1
            probabilities[stream][1] = p2
            weights[stream][0] = w1
            weights[stream][1] = 1.0 - w1

    depletion_scales = [fifo_depletion, lifo_depletion]

    for step in range(lead):
        for stream in range(2):
            if means[stream] > 0.0:
                cumulative = 0.0
                for position in range(m):
                    if stream == 0:
                        index = position
                    else:
                        index = m - 1 - position

                    available = x[index]
                    lower = cumulative
                    upper = cumulative + available
                    expected_lower = 0.0
                    expected_upper = 0.0

                    for component in range(2):
                        p = probabilities[stream][component]
                        r = 1.0 - p
                        mixture_weight = weights[stream][component]

                        lower_integer = int(lower)
                        lower_fraction = lower - float(lower_integer)
                        lower_value = (
                            r * (1.0 - r ** lower_integer) / p
                            + lower_fraction * r ** (lower_integer + 1)
                        )

                        upper_integer = int(upper)
                        upper_fraction = upper - float(upper_integer)
                        upper_value = (
                            r * (1.0 - r ** upper_integer) / p
                            + upper_fraction * r ** (upper_integer + 1)
                        )

                        expected_lower = expected_lower + mixture_weight * lower_value
                        expected_upper = expected_upper + mixture_weight * upper_value

                    consumed = depletion_scales[stream] * (
                        expected_upper - expected_lower
                    )
                    if consumed < 0.0:
                        consumed = 0.0
                    if consumed > available:
                        consumed = available

                    x[index] = available - consumed
                    cumulative = upper

        shifted = [0.0 for i in range(m)]
        for i in range(m - 1):
            shifted[i] = x[i + 1]

        if step < len(pipeline):
            arrival = float(pipeline[step])
            if arrival < 0.0:
                arrival = 0.0
            shifted[m - 1] = arrival
        else:
            shifted[m - 1] = 0.0

        x = shifted

    effective_inventory = 0.0
    for i in range(m):
        if m > 1:
            relative_age = float(i) / float(m - 1)
        else:
            relative_age = 1.0
        inventory_weight = (
            old_weight + (young_weight - old_weight) * relative_age
        )
        effective_inventory = effective_inventory + inventory_weight * x[i]

    order = S - effective_inventory
    if order < 0.0:
        order = 0.0
    if order > Q:
        order = Q
    return float(order)
