def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.1,"max":30.0}
    GAIN = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.2,"max":2.0}
    TAIL = 0.12 # OPT_PARAM: {"type":"float","initial":0.12,"min":0.0,"max":1.5}
    D_SCALE = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.6,"max":1.5}
    SCEN_TAIL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.05,"max":3.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":8.0}
    FRESH_FLOOR = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":1.2}
    SELL_BLEND = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.0}
    RISK = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-3.0,"max":3.0}
    SMOOTH = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":0.8}
    SMOOTH_GATE = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.05,"max":15.0}

    m = len(age)
    if m <= 0:
        return 0.0

    demand_mean = float(mu)
    demand_cv = float(cv)
    if not (demand_mean >= 0.0 and demand_mean < 1.0e10):
        demand_mean = 0.0
    if not (demand_cv >= 0.0 and demand_cv < 1.0e5):
        demand_cv = 0.0

    ff = float(f)
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

    means = [ff * demand_mean, (1.0 - ff) * demand_mean]
    p1s = [1.0, 1.0]
    p2s = [1.0, 1.0]
    r1s = [0.0, 0.0]
    r2s = [0.0, 0.0]
    w1s = [1.0, 1.0]
    supports = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    probabilities = [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    counts = [1, 1]

    for group_index in range(2):
        M = means[group_index]
        if M > 0.0:
            if group_index == 0:
                group_fraction = ff
            else:
                group_fraction = 1.0 - ff

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

            weight1 = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1 = 1.0 - p1
            r2 = 1.0 - p2

            p1s[group_index] = p1
            p2s[group_index] = p2
            r1s[group_index] = r1
            r2s[group_index] = r2
            w1s[group_index] = weight1

            denominator1 = 1.0 + SCEN_TAIL * r1
            denominator2 = 1.0 + SCEN_TAIL * r2
            if denominator1 < 1.0e-12:
                denominator1 = 1.0e-12
            if denominator2 < 1.0e-12:
                denominator2 = 1.0e-12

            mass1 = weight1 * r1 / denominator1
            mass2 = (1.0 - weight1) * r2 / denominator2
            zero_mass = 1.0 - mass1 - mass2
            if zero_mass < 0.0:
                zero_mass = 0.0

            support1 = denominator1 / p1
            support2 = denominator2 / p2

            supports[group_index][0] = 0.0
            supports[group_index][1] = support1
            supports[group_index][2] = support2
            probabilities[group_index][0] = zero_mass
            probabilities[group_index][1] = mass1
            probabilities[group_index][2] = mass2
            counts[group_index] = 3

    projected_mean = 0.0
    projected_second = 0.0
    probability_total = 0.0

    for a0 in range(counts[0]):
        for b0 in range(counts[1]):
            first_probability = (
                probabilities[0][a0] * probabilities[1][b0]
            )
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

                next_arrival = 0.0
                if len(pipeline) > 0:
                    value = float(pipeline[0])
                    if value >= 0.0 and value < 1.0e12:
                        next_arrival = value
                x[m - 1] = x[m - 1] + next_arrival

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

                            freshness_effect = 0.0
                            for i in range(m):
                                freshness = (i + 1.0) / m
                                layer_weight = (
                                    FRESH_FLOOR
                                    + (1.0 - FRESH_FLOOR) * freshness ** A
                                )
                                if layer_weight < 0.0:
                                    layer_weight = 0.0
                                freshness_effect = (
                                    freshness_effect + layer_weight * y[i]
                                )

                            z = [0.0] * m
                            for i in range(m):
                                z[i] = y[i]

                            sellthrough_effect = 0.0
                            for future_period in range(m):
                                for group_index in range(2):
                                    if means[group_index] > 0.0:
                                        p1 = p1s[group_index]
                                        p2 = p2s[group_index]
                                        r1 = r1s[group_index]
                                        r2 = r2s[group_index]
                                        weight1 = w1s[group_index]
                                        cumulative = 0.0

                                        for step in range(m):
                                            if group_index == 0:
                                                idx = step
                                            else:
                                                idx = m - 1 - step

                                            layer = z[idx]
                                            lower = cumulative
                                            upper = cumulative + layer

                                            n0 = int(lower)
                                            fraction0 = lower - n0
                                            if n0 > 0:
                                                h10 = (
                                                    r1
                                                    * (1.0 - r1 ** n0)
                                                    / p1
                                                )
                                                h20 = (
                                                    r2
                                                    * (1.0 - r2 ** n0)
                                                    / p2
                                                )
                                            else:
                                                h10 = 0.0
                                                h20 = 0.0

                                            expected0 = (
                                                weight1
                                                * (
                                                    h10
                                                    + fraction0
                                                    * r1 ** (n0 + 1)
                                                )
                                                + (1.0 - weight1)
                                                * (
                                                    h20
                                                    + fraction0
                                                    * r2 ** (n0 + 1)
                                                )
                                            )

                                            n1 = int(upper)
                                            fraction1 = upper - n1
                                            if n1 > 0:
                                                h11 = (
                                                    r1
                                                    * (1.0 - r1 ** n1)
                                                    / p1
                                                )
                                                h21 = (
                                                    r2
                                                    * (1.0 - r2 ** n1)
                                                    / p2
                                                )
                                            else:
                                                h11 = 0.0
                                                h21 = 0.0

                                            expected1 = (
                                                weight1
                                                * (
                                                    h11
                                                    + fraction1
                                                    * r1 ** (n1 + 1)
                                                )
                                                + (1.0 - weight1)
                                                * (
                                                    h21
                                                    + fraction1
                                                    * r2 ** (n1 + 1)
                                                )
                                            )

                                            depletion = expected1 - expected0
                                            if depletion < 0.0:
                                                depletion = 0.0
                                            if depletion > layer:
                                                depletion = layer

                                            z[idx] = layer - depletion
                                            sellthrough_effect = (
                                                sellthrough_effect + depletion
                                            )
                                            cumulative = upper

                                for i in range(m - 1):
                                    z[i] = z[i + 1]
                                z[m - 1] = 0.0

                            effective = (
                                (1.0 - SELL_BLEND) * freshness_effect
                                + SELL_BLEND * sellthrough_effect
                            )
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
        q = GAIN * gap
    else:
        q = GAIN * C + TAIL * (gap - C)

    if gap > 0.0 and SMOOTH > 0.0 and len(pipeline) > 0:
        previous_order = float(pipeline[len(pipeline) - 1])
        if not (
            previous_order >= 0.0
            and previous_order < 1.0e12
        ):
            previous_order = 0.0
        gate = gap / (gap + SMOOTH_GATE)
        smoothing_weight = SMOOTH * gate
        q = (
            (1.0 - smoothing_weight) * q
            + smoothing_weight * previous_order
        )

    if not (q >= 0.0 and q < 1.0e100):
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
