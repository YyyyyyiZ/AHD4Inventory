def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    TAIL = 0.12 # OPT_PARAM: {"type":"float","initial":0.12,"min":0.0,"max":1.5}
    D_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.55,"max":1.6}
    A = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.1,"max":8.0}
    FRESH_FLOOR = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.5}
    RISK = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.5,"max":2.5}

    m = len(age)
    if m <= 0:
        return 0.0

    demand_mean = float(mu)
    demand_cv = float(cv)
    ff = float(f)

    if not (demand_mean >= 0.0 and demand_mean < 1.0e10):
        demand_mean = 0.0
    if not (demand_cv >= 0.0 and demand_cv < 1.0e5):
        demand_cv = 0.0
    if not (ff >= 0.0):
        ff = 0.0
    if ff > 1.0:
        ff = 1.0

    base = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value >= 0.0 and value < 1.0e12:
            base[i] = value
        else:
            base[i] = 0.0

    supports = [[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]
    probabilities = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
    counts = [1, 1]

    for group_index in range(2):
        if group_index == 0:
            group_fraction = ff
        else:
            group_fraction = 1.0 - ff

        M = group_fraction * demand_mean
        if M > 0.0:
            V = group_fraction * (demand_mean * demand_cv) * (demand_mean * demand_cv)
            aa = V / (M * M) - 1.0 / M
            if aa < 1.0:
                aa = 1.0

            root_argument = aa * aa - 1.0
            if root_argument < 0.0:
                root_argument = 0.0
            root = root_argument ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            if c < 1.0e-12:
                c = 1.0e-12

            mixture_weight = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1 = 1.0 - p1
            r2 = 1.0 - p2

            zero_probability = mixture_weight * p1 + (1.0 - mixture_weight) * p2
            positive_probability = 1.0 - zero_probability
            if positive_probability < 0.0:
                positive_probability = 0.0

            target1 = 0.40 * positive_probability
            target2 = 0.78 * positive_probability
            cut1 = 1
            cut2 = 2
            found1 = 0
            found2 = 0

            for n in range(1, 161):
                cumulative = (
                    mixture_weight * (r1 - r1 ** (n + 1))
                    + (1.0 - mixture_weight) * (r2 - r2 ** (n + 1))
                )
                if found1 == 0 and cumulative >= target1:
                    cut1 = n
                    found1 = 1
                if found2 == 0 and cumulative >= target2:
                    cut2 = n
                    found2 = 1

            if cut2 <= cut1:
                cut2 = cut1 + 1

            cumulative1 = (
                mixture_weight * (r1 - r1 ** (cut1 + 1))
                + (1.0 - mixture_weight) * (r2 - r2 ** (cut1 + 1))
            )
            cumulative2 = (
                mixture_weight * (r1 - r1 ** (cut2 + 1))
                + (1.0 - mixture_weight) * (r2 - r2 ** (cut2 + 1))
            )

            moment11 = (
                r1
                * (
                    1.0
                    - (cut1 + 1.0) * r1 ** cut1
                    + cut1 * r1 ** (cut1 + 1)
                )
                / p1
            )
            moment12 = (
                r2
                * (
                    1.0
                    - (cut1 + 1.0) * r2 ** cut1
                    + cut1 * r2 ** (cut1 + 1)
                )
                / p2
            )
            moment21 = (
                r1
                * (
                    1.0
                    - (cut2 + 1.0) * r1 ** cut2
                    + cut2 * r1 ** (cut2 + 1)
                )
                / p1
            )
            moment22 = (
                r2
                * (
                    1.0
                    - (cut2 + 1.0) * r2 ** cut2
                    + cut2 * r2 ** (cut2 + 1)
                )
                / p2
            )

            first_moment = mixture_weight * moment11 + (1.0 - mixture_weight) * moment12
            second_moment = mixture_weight * moment21 + (1.0 - mixture_weight) * moment22

            low_probability = cumulative1
            middle_probability = cumulative2 - cumulative1
            tail_probability = positive_probability - cumulative2

            if low_probability < 0.0:
                low_probability = 0.0
            if middle_probability < 0.0:
                middle_probability = 0.0
            if tail_probability < 0.0:
                tail_probability = 0.0

            low_mean = first_moment
            middle_mean = second_moment - first_moment
            tail_mean = M - second_moment

            if low_mean < 0.0:
                low_mean = 0.0
            if middle_mean < 0.0:
                middle_mean = 0.0
            if tail_mean < 0.0:
                tail_mean = 0.0

            low_support = 0.0
            middle_support = float(cut1 + 1)
            tail_support = float(cut2 + 1)

            if low_probability > 1.0e-14:
                low_support = low_mean / low_probability
            if middle_probability > 1.0e-14:
                middle_support = middle_mean / middle_probability
            if tail_probability > 1.0e-14:
                tail_support = tail_mean / tail_probability

            supports[group_index][0] = 0.0
            supports[group_index][1] = low_support
            supports[group_index][2] = middle_support
            supports[group_index][3] = tail_support
            probabilities[group_index][0] = zero_probability
            probabilities[group_index][1] = low_probability
            probabilities[group_index][2] = middle_probability
            probabilities[group_index][3] = tail_probability
            counts[group_index] = 4

    next_arrival = 0.0
    if len(pipeline) > 0:
        arrival_value = float(pipeline[0])
        if arrival_value >= 0.0 and arrival_value < 1.0e12:
            next_arrival = arrival_value

    projected_mean = 0.0
    projected_second = 0.0
    probability_total = 0.0

    for fifo0 in range(counts[0]):
        for lifo0 in range(counts[1]):
            first_probability = (
                probabilities[0][fifo0] * probabilities[1][lifo0]
            )
            if first_probability > 0.0:
                x = [0.0] * m
                for i in range(m):
                    x[i] = base[i]

                remaining = D_SCALE * supports[0][fifo0]
                for i in range(m):
                    used = x[i]
                    if used > remaining:
                        used = remaining
                    if used < 0.0:
                        used = 0.0
                    x[i] = x[i] - used
                    remaining = remaining - used

                remaining = D_SCALE * supports[1][lifo0]
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
                x[m - 1] = next_arrival

                for fifo1 in range(counts[0]):
                    for lifo1 in range(counts[1]):
                        scenario_probability = (
                            first_probability
                            * probabilities[0][fifo1]
                            * probabilities[1][lifo1]
                        )

                        if scenario_probability > 0.0:
                            y = [0.0] * m
                            for i in range(m):
                                y[i] = x[i]

                            remaining = D_SCALE * supports[0][fifo1]
                            for i in range(m):
                                used = y[i]
                                if used > remaining:
                                    used = remaining
                                if used < 0.0:
                                    used = 0.0
                                y[i] = y[i] - used
                                remaining = remaining - used

                            remaining = D_SCALE * supports[1][lifo1]
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
                                weight = (
                                    FRESH_FLOOR
                                    + (1.0 - FRESH_FLOOR) * freshness ** A
                                )
                                if weight < 0.0:
                                    weight = 0.0
                                effective = effective + weight * y[i]

                            projected_mean = (
                                projected_mean
                                + scenario_probability * effective
                            )
                            projected_second = (
                                projected_second
                                + scenario_probability * effective * effective
                            )
                            probability_total = (
                                probability_total + scenario_probability
                            )

    if probability_total > 0.0:
        projected_mean = projected_mean / probability_total
        projected_second = projected_second / probability_total
    else:
        projected_mean = 0.0
        projected_second = 0.0

    variance = projected_second - projected_mean * projected_mean
    if variance < 0.0:
        variance = 0.0

    certainty_equivalent = projected_mean + RISK * variance ** 0.5
    gap = S - certainty_equivalent

    if gap <= 0.0:
        q = 0.0
    elif gap <= C:
        q = gap
    else:
        q = C + TAIL * (gap - C)

    if not (q >= 0.0 and q < 1.0e100):
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0

    return float(q)
