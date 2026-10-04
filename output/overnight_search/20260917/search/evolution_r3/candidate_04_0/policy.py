def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    TAIL = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.5}
    D_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.6,"max":1.5}
    SPLIT = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.2,"max":0.85}
    ALPHA = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.2,"max":0.8}
    QBLEND = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":1.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":8.0}
    FRESH_FLOOR = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.5}

    m = len(age)
    ff = float(f)
    if not (ff >= 0.0):
        ff = 0.0
    if ff > 1.0:
        ff = 1.0

    base = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value >= 0.0 and value < 1.0e100:
            base[i] = value
        else:
            base[i] = 0.0

    supports = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    probabilities = [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    counts = [1, 1]

    for group_index in range(2):
        if group_index == 0:
            g = ff
        else:
            g = 1.0 - ff

        M = g * float(mu)
        if M > 0.0:
            V = g * (float(mu) * float(cv)) * (float(mu) * float(cv))
            aa = V / (M * M) - 1.0 / M
            if aa < 1.0:
                aa = 1.0

            root = (aa * aa - 1.0) ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            mixture_weight = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1 = 1.0 - p1
            r2 = 1.0 - p2

            zero_probability = mixture_weight * p1 + (1.0 - mixture_weight) * p2
            positive_probability = 1.0 - zero_probability
            target_probability = SPLIT * positive_probability

            cut = 1
            best_error = 1.0e100
            for n in range(1, 81):
                low_probability_n = (
                    mixture_weight * (r1 - r1 ** (n + 1))
                    + (1.0 - mixture_weight) * (r2 - r2 ** (n + 1))
                )
                error = low_probability_n - target_probability
                if error < 0.0:
                    error = -error
                if error < best_error:
                    best_error = error
                    cut = n

            low_probability = (
                mixture_weight * (r1 - r1 ** (cut + 1))
                + (1.0 - mixture_weight) * (r2 - r2 ** (cut + 1))
            )
            tail_probability = positive_probability - low_probability
            if tail_probability < 0.0:
                tail_probability = 0.0

            low_mean1 = (
                r1
                * (1.0 - (cut + 1.0) * r1 ** cut + cut * r1 ** (cut + 1))
                / p1
            )
            low_mean2 = (
                r2
                * (1.0 - (cut + 1.0) * r2 ** cut + cut * r2 ** (cut + 1))
                / p2
            )
            low_mean = mixture_weight * low_mean1 + (1.0 - mixture_weight) * low_mean2
            tail_mean = M - low_mean
            if tail_mean < 0.0:
                tail_mean = 0.0

            low_support = 0.0
            if low_probability > 1.0e-14:
                low_support = low_mean / low_probability

            tail_support = low_support
            if tail_probability > 1.0e-14:
                tail_support = tail_mean / tail_probability

            supports[group_index][0] = 0.0
            supports[group_index][1] = low_support
            supports[group_index][2] = tail_support
            probabilities[group_index][0] = zero_probability
            probabilities[group_index][1] = low_probability
            probabilities[group_index][2] = tail_probability
            counts[group_index] = 3

    requirements = [0.0] * 81
    scenario_weights = [0.0] * 81
    scenario_count = 0
    probability_total = 0.0
    requirement_mean = 0.0

    for a0 in range(counts[0]):
        for b0 in range(counts[1]):
            first_probability = probabilities[0][a0] * probabilities[1][b0]
            if first_probability > 0.0:
                x = [0.0] * m
                for i in range(m):
                    x[i] = base[i]

                remaining = D_SCALE * supports[0][a0]
                for i in range(m):
                    used = x[i]
                    if used > remaining:
                        used = remaining
                    if used < 0.0:
                        used = 0.0
                    x[i] = x[i] - used
                    remaining = remaining - used

                remaining = D_SCALE * supports[1][b0]
                for step in range(m):
                    idx = m - 1 - step
                    used = x[idx]
                    if used > remaining:
                        used = remaining
                    if used < 0.0:
                        used = 0.0
                    x[idx] = x[idx] - used
                    remaining = remaining - used

                for i in range(m - 1):
                    x[i] = x[i + 1]
                x[m - 1] = 0.0

                arrival = 0.0
                if len(pipeline) > 0:
                    arrival_value = float(pipeline[0])
                    if arrival_value >= 0.0 and arrival_value < 1.0e100:
                        arrival = arrival_value
                x[m - 1] = x[m - 1] + arrival

                for a1 in range(counts[0]):
                    for b1 in range(counts[1]):
                        scenario_probability = (
                            first_probability
                            * probabilities[0][a1]
                            * probabilities[1][b1]
                        )
                        if scenario_probability > 0.0:
                            y = [0.0] * m
                            for i in range(m):
                                y[i] = x[i]

                            remaining = D_SCALE * supports[0][a1]
                            for i in range(m):
                                used = y[i]
                                if used > remaining:
                                    used = remaining
                                if used < 0.0:
                                    used = 0.0
                                y[i] = y[i] - used
                                remaining = remaining - used

                            remaining = D_SCALE * supports[1][b1]
                            for step in range(m):
                                idx = m - 1 - step
                                used = y[idx]
                                if used > remaining:
                                    used = remaining
                                if used < 0.0:
                                    used = 0.0
                                y[idx] = y[idx] - used
                                remaining = remaining - used

                            for i in range(m - 1):
                                y[i] = y[i + 1]
                            y[m - 1] = 0.0

                            effective = 0.0
                            for i in range(m):
                                freshness = (i + 1.0) / m
                                inventory_weight = (
                                    FRESH_FLOOR
                                    + (1.0 - FRESH_FLOOR) * freshness ** A
                                )
                                if inventory_weight < 0.0:
                                    inventory_weight = 0.0
                                effective = effective + inventory_weight * y[i]

                            requirement = S - effective
                            requirements[scenario_count] = requirement
                            scenario_weights[scenario_count] = scenario_probability
                            scenario_count = scenario_count + 1
                            probability_total = probability_total + scenario_probability
                            requirement_mean = (
                                requirement_mean + scenario_probability * requirement
                            )

    if scenario_count <= 0 or probability_total <= 0.0:
        raw_gap = S
    else:
        requirement_mean = requirement_mean / probability_total
        lower = requirements[0]
        upper = requirements[0]

        for i in range(1, scenario_count):
            if requirements[i] < lower:
                lower = requirements[i]
            if requirements[i] > upper:
                upper = requirements[i]

        for iteration in range(18):
            midpoint = 0.5 * (lower + upper)
            cumulative_probability = 0.0
            for i in range(scenario_count):
                if requirements[i] <= midpoint:
                    cumulative_probability = (
                        cumulative_probability + scenario_weights[i]
                    )
            cumulative_probability = cumulative_probability / probability_total
            if cumulative_probability < ALPHA:
                lower = midpoint
            else:
                upper = midpoint

        quantile_requirement = 0.5 * (lower + upper)
        raw_gap = (
            QBLEND * quantile_requirement
            + (1.0 - QBLEND) * requirement_mean
        )

    if raw_gap <= 0.0:
        q = 0.0
    elif raw_gap <= C:
        q = raw_gap
    else:
        q = C + TAIL * (raw_gap - C)

    if not (q >= 0.0):
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
