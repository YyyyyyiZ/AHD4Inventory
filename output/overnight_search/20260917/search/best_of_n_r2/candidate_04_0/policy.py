def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    depletion_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.35,"max":1.8}
    old_credit = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":1.0}
    life_power = 1.3 # OPT_PARAM: {"type":"float","initial":1.3,"min":0.1,"max":4.0}
    survivor_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.6}
    order_gain = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.3,"max":1.8}

    m = len(age)
    state = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value < 0.0:
            value = 0.0
        state[i] = value

    base_variance = (mu * cv) * (mu * cv)

    mean_fifo = f * mu
    if mean_fifo > 0.0:
        variance_fifo = f * base_variance
        a_fifo = variance_fifo / (mean_fifo * mean_fifo) - 1.0 / mean_fifo
        disc_fifo = a_fifo * a_fifo - 1.0
        if disc_fifo < 0.0:
            disc_fifo = 0.0
        root_fifo = disc_fifo ** 0.5
        b_fifo = 1.0 + a_fifo + root_fifo
        c_fifo = 1.0 + a_fifo - root_fifo
        weight_fifo = 1.0 / b_fifo
        p1_fifo = 2.0 / (2.0 + mean_fifo * b_fifo)
        p2_fifo = 2.0 / (2.0 + mean_fifo * c_fifo)
        r1_fifo = 1.0 - p1_fifo
        r2_fifo = 1.0 - p2_fifo
    else:
        weight_fifo = 0.0
        r1_fifo = 0.0
        r2_fifo = 0.0

    lifo_share = 1.0 - f
    mean_lifo = lifo_share * mu
    if mean_lifo > 0.0:
        variance_lifo = lifo_share * base_variance
        a_lifo = variance_lifo / (mean_lifo * mean_lifo) - 1.0 / mean_lifo
        disc_lifo = a_lifo * a_lifo - 1.0
        if disc_lifo < 0.0:
            disc_lifo = 0.0
        root_lifo = disc_lifo ** 0.5
        b_lifo = 1.0 + a_lifo + root_lifo
        c_lifo = 1.0 + a_lifo - root_lifo
        weight_lifo = 1.0 / b_lifo
        p1_lifo = 2.0 / (2.0 + mean_lifo * b_lifo)
        p2_lifo = 2.0 / (2.0 + mean_lifo * c_lifo)
        r1_lifo = 1.0 - p1_lifo
        r2_lifo = 1.0 - p2_lifo
    else:
        weight_lifo = 0.0
        r1_lifo = 0.0
        r2_lifo = 0.0

    for step in range(L):
        if step > 0:
            pipe_index = step - 1
            if pipe_index < len(pipeline):
                arrival = float(pipeline[pipe_index])
                if arrival > 0.0:
                    state[m - 1] = state[m - 1] + arrival

        if mean_fifo > 0.0:
            cumulative = 0.0
            for i in range(m):
                stock = state[i]
                upper = cumulative + stock

                lower_integer = int(cumulative)
                lower_fraction = cumulative - float(lower_integer)
                lower_geom1 = (
                    r1_fifo * (1.0 - r1_fifo ** lower_integer) / (1.0 - r1_fifo)
                    + lower_fraction * r1_fifo ** (lower_integer + 1)
                )
                lower_geom2 = (
                    r2_fifo * (1.0 - r2_fifo ** lower_integer) / (1.0 - r2_fifo)
                    + lower_fraction * r2_fifo ** (lower_integer + 1)
                )
                lower_fill = (
                    weight_fifo * lower_geom1
                    + (1.0 - weight_fifo) * lower_geom2
                )

                upper_integer = int(upper)
                upper_fraction = upper - float(upper_integer)
                upper_geom1 = (
                    r1_fifo * (1.0 - r1_fifo ** upper_integer) / (1.0 - r1_fifo)
                    + upper_fraction * r1_fifo ** (upper_integer + 1)
                )
                upper_geom2 = (
                    r2_fifo * (1.0 - r2_fifo ** upper_integer) / (1.0 - r2_fifo)
                    + upper_fraction * r2_fifo ** (upper_integer + 1)
                )
                upper_fill = (
                    weight_fifo * upper_geom1
                    + (1.0 - weight_fifo) * upper_geom2
                )

                consumed = depletion_scale * (upper_fill - lower_fill)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > stock:
                    consumed = stock
                state[i] = stock - consumed
                cumulative = upper

        if mean_lifo > 0.0:
            cumulative = 0.0
            for i in range(m - 1, -1, -1):
                stock = state[i]
                upper = cumulative + stock

                lower_integer = int(cumulative)
                lower_fraction = cumulative - float(lower_integer)
                lower_geom1 = (
                    r1_lifo * (1.0 - r1_lifo ** lower_integer) / (1.0 - r1_lifo)
                    + lower_fraction * r1_lifo ** (lower_integer + 1)
                )
                lower_geom2 = (
                    r2_lifo * (1.0 - r2_lifo ** lower_integer) / (1.0 - r2_lifo)
                    + lower_fraction * r2_lifo ** (lower_integer + 1)
                )
                lower_fill = (
                    weight_lifo * lower_geom1
                    + (1.0 - weight_lifo) * lower_geom2
                )

                upper_integer = int(upper)
                upper_fraction = upper - float(upper_integer)
                upper_geom1 = (
                    r1_lifo * (1.0 - r1_lifo ** upper_integer) / (1.0 - r1_lifo)
                    + upper_fraction * r1_lifo ** (upper_integer + 1)
                )
                upper_geom2 = (
                    r2_lifo * (1.0 - r2_lifo ** upper_integer) / (1.0 - r2_lifo)
                    + upper_fraction * r2_lifo ** (upper_integer + 1)
                )
                upper_fill = (
                    weight_lifo * upper_geom1
                    + (1.0 - weight_lifo) * upper_geom2
                )

                consumed = depletion_scale * (upper_fill - lower_fill)
                if consumed < 0.0:
                    consumed = 0.0
                if consumed > stock:
                    consumed = stock
                state[i] = stock - consumed
                cumulative = upper

        for i in range(m - 1):
            state[i] = state[i + 1]
        state[m - 1] = 0.0

    effective_inventory = 0.0
    for i in range(m):
        relative_life = float(i + 1) / float(m)
        age_weight = old_credit + (1.0 - old_credit) * relative_life ** life_power
        effective_inventory = (
            effective_inventory
            + survivor_credit * age_weight * state[i]
        )

    gap = S - effective_inventory
    if gap <= 0.0:
        return 0.0

    order = order_gain * gap
    if order != order:
        return 0.0
    if order > 1000000.0:
        order = 1000000.0
    return float(order)
