def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    demand_scale = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.6,"max":1.4}
    level_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":2.5}
    linear_age = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":-1.0,"max":4.0}
    quadratic_age = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-1.0,"max":4.0}
    uncertain_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}

    m = len(age)
    lead = int(L)
    stochastic = [0.0] * m
    fluid = [0.0] * m

    for i in range(m):
        x = float(age[i])
        if x < 0.0:
            x = 0.0
        stochastic[i] = x
        fluid[i] = x

    for t in range(lead):
        for stream in range(2):
            if stream == 0:
                g = float(f)
            else:
                g = 1.0 - float(f)

            if g > 0.0:
                M = g * float(mu)
                V = g * (float(mu) * float(cv)) ** 2
                a = V / (M * M) - 1.0 / M
                disc = a * a - 1.0
                if disc < 0.0:
                    disc = 0.0
                root = disc ** 0.5
                b = 1.0 + a + root
                c = 1.0 + a - root
                weight1 = 1.0 / b
                weight2 = 1.0 - weight1
                p1 = 2.0 / (2.0 + M * b)
                p2 = 2.0 / (2.0 + M * c)
                r1 = 1.0 - p1
                r2 = 1.0 - p2

                new_state = [0.0] * m
                cumulative = 0.0
                phi_before = 0.0

                for k in range(m):
                    if stream == 0:
                        idx = k
                    else:
                        idx = m - 1 - k

                    bucket = stochastic[idx]
                    cumulative_after = cumulative + bucket
                    y = cumulative_after / demand_scale
                    n = int(y)
                    fraction = y - float(n)

                    if n > 0:
                        truncated1 = r1 * (1.0 - r1 ** n) / p1
                        truncated2 = r2 * (1.0 - r2 ** n) / p2
                    else:
                        truncated1 = 0.0
                        truncated2 = 0.0

                    h_integer = float(n) - weight1 * truncated1 - weight2 * truncated2
                    cdf_n = weight1 * (1.0 - r1 ** (n + 1)) + weight2 * (1.0 - r2 ** (n + 1))
                    phi_after = demand_scale * (h_integer + fraction * cdf_n)
                    remaining = phi_after - phi_before

                    if remaining < 0.0:
                        remaining = 0.0
                    if remaining > bucket:
                        remaining = bucket

                    new_state[idx] = remaining
                    cumulative = cumulative_after
                    phi_before = phi_after

                stochastic = new_state

                demand_left = demand_scale * M
                for k in range(m):
                    if stream == 0:
                        idx = k
                    else:
                        idx = m - 1 - k

                    bucket = fluid[idx]
                    if demand_left > 0.0:
                        if bucket <= demand_left:
                            fluid[idx] = 0.0
                            demand_left = demand_left - bucket
                        else:
                            fluid[idx] = bucket - demand_left
                            demand_left = 0.0

        shifted_stochastic = [0.0] * m
        shifted_fluid = [0.0] * m

        for i in range(m - 1):
            shifted_stochastic[i] = stochastic[i + 1]
            shifted_fluid[i] = fluid[i + 1]

        if t < len(pipeline):
            arrival = float(pipeline[t])
            if arrival < 0.0:
                arrival = 0.0
        else:
            arrival = 0.0

        shifted_stochastic[m - 1] = arrival
        shifted_fluid[m - 1] = arrival
        stochastic = shifted_stochastic
        fluid = shifted_fluid

    weighted_stochastic = 0.0
    weighted_fluid = 0.0

    for i in range(m):
        if m > 1:
            oldness = float(m - 1 - i) / float(m - 1)
        else:
            oldness = 0.0

        age_weight = level_credit * (
            1.0 + linear_age * oldness + quadratic_age * oldness * oldness
        )
        weighted_stochastic = weighted_stochastic + age_weight * stochastic[i]
        weighted_fluid = weighted_fluid + age_weight * fluid[i]

    projected_credit = weighted_fluid + uncertain_credit * (
        weighted_stochastic - weighted_fluid
    )
    q = S - projected_credit

    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0

    return float(q)
