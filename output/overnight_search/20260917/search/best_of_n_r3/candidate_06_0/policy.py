def compute_order_amount(age, pipeline, mu, cv, f, L):
    import math

    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    W0 = 0.35 # OPT_PARAM: {"type":"float","initial":0.35,"min":0.0,"max":2.0}
    W1 = 0.60 # OPT_PARAM: {"type":"float","initial":0.60,"min":0.0,"max":2.0}
    W2 = 0.80 # OPT_PARAM: {"type":"float","initial":0.80,"min":0.0,"max":2.0}
    W3 = 1.00 # OPT_PARAM: {"type":"float","initial":1.00,"min":0.0,"max":2.0}

    m = len(age)
    if m <= 0:
        return 0.0

    x = [0.0] * m
    for i in range(m):
        value = float(age[i])
        if not math.isfinite(value) or value < 0.0:
            value = 0.0
        x[i] = value

    mf = float(f) * float(mu)
    vf = float(f) * (float(mu) * float(cv)) ** 2
    ml = (1.0 - float(f)) * float(mu)
    vl = (1.0 - float(f)) * (float(mu) * float(cv)) ** 2

    wf = 1.0
    pf1 = 1.0
    pf2 = 1.0
    rf1 = 0.0
    rf2 = 0.0
    if mf > 0.0:
        af = vf / (mf * mf) - 1.0 / mf
        if af < 1.0:
            af = 1.0
        rootf = math.sqrt(max(0.0, af * af - 1.0))
        bf = 1.0 + af + rootf
        cf = 1.0 + af - rootf
        wf = 1.0 / bf
        pf1 = 2.0 / (2.0 + mf * bf)
        pf2 = 2.0 / (2.0 + mf * cf)
        rf1 = 1.0 - pf1
        rf2 = 1.0 - pf2

    wl = 1.0
    pl1 = 1.0
    pl2 = 1.0
    rl1 = 0.0
    rl2 = 0.0
    if ml > 0.0:
        al = vl / (ml * ml) - 1.0 / ml
        if al < 1.0:
            al = 1.0
        rootl = math.sqrt(max(0.0, al * al - 1.0))
        bl = 1.0 + al + rootl
        cl = 1.0 + al - rootl
        wl = 1.0 / bl
        pl1 = 2.0 / (2.0 + ml * bl)
        pl2 = 2.0 / (2.0 + ml * cl)
        rl1 = 1.0 - pl1
        rl2 = 1.0 - pl2

    lead = int(L)
    if lead < 0:
        lead = 0
    if lead > 6:
        lead = 6

    for step in range(6):
        if step >= lead:
            break

        total = 0.0
        for i in range(m):
            total = total + x[i]

        after_demand = [0.0] * m

        if total > 0.0:
            if mf <= 0.0:
                max_fifo_demand = 1
            else:
                max_fifo_demand = int(math.ceil(total))
                if max_fifo_demand < 1:
                    max_fifo_demand = 1

            for demand_f in range(256):
                if demand_f >= max_fifo_demand:
                    break

                if mf <= 0.0:
                    probability_f = 1.0
                else:
                    probability_f = (
                        wf * pf1 * (rf1 ** demand_f)
                        + (1.0 - wf) * pf2 * (rf2 ** demand_f)
                    )

                remaining_f = float(demand_f)
                after_fifo = [0.0] * m
                for i in range(m):
                    available = x[i]
                    if remaining_f >= available:
                        after_fifo[i] = 0.0
                        remaining_f = remaining_f - available
                    else:
                        after_fifo[i] = available - remaining_f
                        remaining_f = 0.0

                cumulative = 0.0
                previous_expected = 0.0
                for reverse_i in range(m):
                    i = m - 1 - reverse_i
                    cumulative = cumulative + after_fifo[i]

                    if ml <= 0.0:
                        expected_cumulative = cumulative
                    else:
                        integer_part = int(math.floor(cumulative))
                        fractional_part = cumulative - float(integer_part)

                        truncated_mean1 = (
                            rl1 * (1.0 - rl1 ** integer_part) / (1.0 - rl1)
                            + fractional_part * rl1 ** (integer_part + 1)
                        )
                        truncated_mean2 = (
                            rl2 * (1.0 - rl2 ** integer_part) / (1.0 - rl2)
                            + fractional_part * rl2 ** (integer_part + 1)
                        )
                        expected_cumulative = cumulative - (
                            wl * truncated_mean1
                            + (1.0 - wl) * truncated_mean2
                        )
                        if expected_cumulative < 0.0:
                            expected_cumulative = 0.0

                    expected_segment = expected_cumulative - previous_expected
                    if expected_segment < 0.0:
                        expected_segment = 0.0
                    after_demand[i] = (
                        after_demand[i] + probability_f * expected_segment
                    )
                    previous_expected = expected_cumulative

        shifted = [0.0] * m
        for i in range(1, m):
            shifted[i - 1] = after_demand[i]

        if step < len(pipeline):
            arrival = float(pipeline[step])
            if not math.isfinite(arrival) or arrival < 0.0:
                arrival = 0.0
            shifted[m - 1] = shifted[m - 1] + arrival

        x = shifted

    weighted_projected_stock = 0.0
    for i in range(m):
        if i == 0:
            weight = W0
        elif i == 1:
            weight = W1
        elif i == 2:
            weight = W2
        else:
            weight = W3
        weighted_projected_stock = weighted_projected_stock + weight * x[i]

    order = S - weighted_projected_stock
    if not math.isfinite(order) or order <= 0.0:
        return 0.0
    return float(order)
