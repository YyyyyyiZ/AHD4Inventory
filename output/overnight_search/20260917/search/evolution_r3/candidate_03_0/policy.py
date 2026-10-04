def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.4,"max":1.8}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.1,"max":8.0}
    FRESH_FLOOR = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.0}
    RISK = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-2.0,"max":2.0}
    TAIL = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}

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

    means = [ff * mu, (1.0 - ff) * mu]
    p1s = [1.0, 1.0]
    p2s = [1.0, 1.0]
    r1s = [0.0, 0.0]
    r2s = [0.0, 0.0]
    w1s = [1.0, 1.0]

    support0 = [0.0, 0.0, 0.0]
    support1 = [0.0, 0.0, 0.0]
    prob0 = [1.0, 0.0, 0.0]
    prob1 = [1.0, 0.0, 0.0]
    count0 = 1
    count1 = 1

    for group_index in range(2):
        M = means[group_index]
        if M > 0.0:
            g = ff
            if group_index == 1:
                g = 1.0 - ff

            V = g * (mu * cv) * (mu * cv)
            aa = V / (M * M) - 1.0 / M
            if aa < 1.0:
                aa = 1.0

            root = (aa * aa - 1.0) ** 0.5
            b = 1.0 + aa + root
            c = 1.0 + aa - root
            w1 = 1.0 / b
            p1 = 2.0 / (2.0 + M * b)
            p2 = 2.0 / (2.0 + M * c)
            r1 = 1.0 - p1
            r2 = 1.0 - p2

            p1s[group_index] = p1
            p2s[group_index] = p2
            r1s[group_index] = r1
            r2s[group_index] = r2
            w1s[group_index] = w1

            mass1 = w1 * r1 / (1.0 + r1)
            mass2 = (1.0 - w1) * r2 / (1.0 + r2)
            zero_mass = 1.0 - mass1 - mass2
            demand1 = (1.0 + r1) / p1
            demand2 = (1.0 + r2) / p2

            if group_index == 0:
                support0[0] = 0.0
                support0[1] = demand1
                support0[2] = demand2
                prob0[0] = zero_mass
                prob0[1] = mass1
                prob0[2] = mass2
                count0 = 3
            else:
                support1[0] = 0.0
                support1[1] = demand1
                support1[2] = demand2
                prob1[0] = zero_mass
                prob1[1] = mass1
                prob1[2] = mass2
                count1 = 3

    projected_mean = 0.0
    projected_second = 0.0
    probability_total = 0.0

    for u in range(count0):
        for v in range(count1):
            scenario_probability = prob0[u] * prob1[v]
            if scenario_probability > 0.0:
                x = [0.0] * m
                for i in range(m):
                    x[i] = base[i]

                remaining = support0[u]
                for i in range(m):
                    layer = x[i]
                    used = layer
                    if used > remaining:
                        used = remaining
                    if used < 0.0:
                        used = 0.0
                    x[i] = layer - used
                    remaining = remaining - used

                remaining = support1[v]
                for step in range(m):
                    idx = m - 1 - step
                    layer = x[idx]
                    used = layer
                    if used > remaining:
                        used = remaining
                    if used < 0.0:
                        used = 0.0
                    x[idx] = layer - used
                    remaining = remaining - used

                for i in range(m - 1):
                    x[i] = x[i + 1]
                x[m - 1] = 0.0

                for t in range(1, L):
                    if t - 1 < len(pipeline):
                        arrival = float(pipeline[t - 1])
                        if not (arrival >= 0.0 and arrival < 1.0e100):
                            arrival = 0.0
                        x[m - 1] = x[m - 1] + arrival

                    for group_index in range(2):
                        if means[group_index] > 0.0:
                            p1 = p1s[group_index]
                            p2 = p2s[group_index]
                            r1 = r1s[group_index]
                            r2 = r2s[group_index]
                            w1 = w1s[group_index]
                            cumulative = 0.0

                            for step in range(m):
                                idx = step
                                if group_index == 1:
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
                                expected0 = (
                                    w1 * (h10 + frac0 * r1 ** (n0 + 1))
                                    + (1.0 - w1) * (h20 + frac0 * r2 ** (n0 + 1))
                                )

                                n1 = int(upper)
                                frac1 = upper - n1
                                if n1 > 0:
                                    h11 = r1 * (1.0 - r1 ** n1) / p1
                                    h21 = r2 * (1.0 - r2 ** n1) / p2
                                else:
                                    h11 = 0.0
                                    h21 = 0.0
                                expected1 = (
                                    w1 * (h11 + frac1 * r1 ** (n1 + 1))
                                    + (1.0 - w1) * (h21 + frac1 * r2 ** (n1 + 1))
                                )

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

                effective = 0.0
                for i in range(m):
                    freshness = (i + 1.0) / m
                    weight = FRESH_FLOOR + (1.0 - FRESH_FLOOR) * freshness ** A
                    effective = effective + weight * x[i]

                projected_mean = projected_mean + scenario_probability * effective
                projected_second = projected_second + scenario_probability * effective * effective
                probability_total = probability_total + scenario_probability

    if probability_total > 0.0:
        projected_mean = projected_mean / probability_total
        projected_second = projected_second / probability_total

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

    if not (q >= 0.0):
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
