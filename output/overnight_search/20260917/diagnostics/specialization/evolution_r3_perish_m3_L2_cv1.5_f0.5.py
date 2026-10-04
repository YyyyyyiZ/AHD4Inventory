def compute_order_amount(age, pipeline, _opt_values):
    mu = 4.0
    cv = 1.5
    f = 0.5
    L = 2
    S = _opt_values[0]
    C = _opt_values[1]
    GAIN = _opt_values[2]
    TAIL = _opt_values[3]
    K = _opt_values[4]
    SCEN_TAIL = _opt_values[5]
    A = _opt_values[6]
    FRESH_FLOOR = _opt_values[7]
    SELL_BLEND = _opt_values[8]
    RISK = _opt_values[9]
    m = len(age)
    if m <= 0:
        return 0.0
    ff = float(f)
    if not ff >= 0.0:
        ff = 0.0
    if ff > 1.0:
        ff = 1.0
    demand_mean = float(mu)
    demand_cv = float(cv)
    if not (demand_mean >= 0.0 and demand_mean < 10000000000.0):
        demand_mean = 0.0
    if not (demand_cv >= 0.0 and demand_cv < 100000.0):
        demand_cv = 0.0
    base = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if value >= 0.0 and value < 1000000000000.0:
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
            if c < 1e-12:
                c = 1e-12
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
            if denominator1 < 1e-12:
                denominator1 = 1e-12
            if denominator2 < 1e-12:
                denominator2 = 1e-12
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
    for scenario0 in range(counts[0]):
        for scenario1 in range(counts[1]):
            scenario_probability = probabilities[0][scenario0] * probabilities[1][scenario1]
            if scenario_probability > 0.0:
                x = [0.0] * m
                for i in range(m):
                    x[i] = base[i]
                remaining = supports[0][scenario0]
                for i in range(m):
                    used = x[i]
                    if used > remaining:
                        used = remaining
                    if used < 0.0:
                        used = 0.0
                    x[i] = x[i] - used
                    remaining = remaining - used
                remaining = supports[1][scenario1]
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
                for t in range(1, L):
                    pipeline_index = t - 1
                    if pipeline_index < len(pipeline):
                        arrival = float(pipeline[pipeline_index])
                        if not (arrival >= 0.0 and arrival < 1000000000000.0):
                            arrival = 0.0
                        x[m - 1] = x[m - 1] + arrival
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
                                layer = x[idx]
                                lower = cumulative
                                upper = cumulative + layer
                                n0 = int(lower)
                                frac0 = lower - n0
                                if n0 > 0:
                                    h10 = r1 * (1.0 - r1 ** n0) / p1
                                    h20 = r2 * (1.0 - r2 ** n0) / p2
                                else:
                                    h10 = 0.0
                                    h20 = 0.0
                                expected0 = weight1 * (h10 + frac0 * r1 ** (n0 + 1)) + (1.0 - weight1) * (h20 + frac0 * r2 ** (n0 + 1))
                                n1 = int(upper)
                                frac1 = upper - n1
                                if n1 > 0:
                                    h11 = r1 * (1.0 - r1 ** n1) / p1
                                    h21 = r2 * (1.0 - r2 ** n1) / p2
                                else:
                                    h11 = 0.0
                                    h21 = 0.0
                                expected1 = weight1 * (h11 + frac1 * r1 ** (n1 + 1)) + (1.0 - weight1) * (h21 + frac1 * r2 ** (n1 + 1))
                                depletion = K * (expected1 - expected0)
                                if depletion < 0.0:
                                    depletion = 0.0
                                if depletion > layer:
                                    depletion = layer
                                x[idx] = layer - depletion
                                cumulative = upper
                    for i in range(m - 1):
                        x[i] = x[i + 1]
                    x[m - 1] = 0.0
                freshness_effect = 0.0
                for i in range(m):
                    freshness = (i + 1.0) / m
                    layer_weight = FRESH_FLOOR + (1.0 - FRESH_FLOOR) * freshness ** A
                    if layer_weight < 0.0:
                        layer_weight = 0.0
                    freshness_effect = freshness_effect + layer_weight * x[i]
                z = [0.0] * m
                for i in range(m):
                    z[i] = x[i]
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
                                frac0 = lower - n0
                                if n0 > 0:
                                    h10 = r1 * (1.0 - r1 ** n0) / p1
                                    h20 = r2 * (1.0 - r2 ** n0) / p2
                                else:
                                    h10 = 0.0
                                    h20 = 0.0
                                expected0 = weight1 * (h10 + frac0 * r1 ** (n0 + 1)) + (1.0 - weight1) * (h20 + frac0 * r2 ** (n0 + 1))
                                n1 = int(upper)
                                frac1 = upper - n1
                                if n1 > 0:
                                    h11 = r1 * (1.0 - r1 ** n1) / p1
                                    h21 = r2 * (1.0 - r2 ** n1) / p2
                                else:
                                    h11 = 0.0
                                    h21 = 0.0
                                expected1 = weight1 * (h11 + frac1 * r1 ** (n1 + 1)) + (1.0 - weight1) * (h21 + frac1 * r2 ** (n1 + 1))
                                depletion = expected1 - expected0
                                if depletion < 0.0:
                                    depletion = 0.0
                                if depletion > layer:
                                    depletion = layer
                                z[idx] = layer - depletion
                                sellthrough_effect = sellthrough_effect + depletion
                                cumulative = upper
                    for i in range(m - 1):
                        z[i] = z[i + 1]
                    z[m - 1] = 0.0
                effective = (1.0 - SELL_BLEND) * freshness_effect + SELL_BLEND * sellthrough_effect
                projected_mean = projected_mean + scenario_probability * effective
                projected_second = projected_second + scenario_probability * effective * effective
                probability_total = probability_total + scenario_probability
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
    if not (q >= 0.0 and q < 1e+100):
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)