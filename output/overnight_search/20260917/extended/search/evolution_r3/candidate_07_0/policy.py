def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 18.0 # OPT_PARAM: {"type":"float","initial":18.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":50.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    GF = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    GL = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    W0 = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":4.0}
    W1 = 0.55 # OPT_PARAM: {"type":"float","initial":0.55,"min":0.0,"max":4.0}
    W2 = 0.80 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":4.0}
    W3 = 0.95 # OPT_PARAM: {"type":"float","initial":0.95,"min":0.0,"max":4.0}
    W4 = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    CUR = 0.10 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.5}
    MED = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":-1.0,"max":2.0}
    J = 2.5 # OPT_PARAM: {"type":"float","initial":2.5,"min":0.0,"max":10.0}
    RISK_SCALE = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.05,"max":8.0}

    m = len(age)
    if m <= 0:
        return 0.0

    demand_mean = float(mu)
    demand_cv = float(cv)
    f_use = float(f)

    if demand_mean != demand_mean or demand_mean < 0.0:
        demand_mean = 0.0
    if demand_cv != demand_cv or demand_cv < 0.0:
        demand_cv = 0.0
    if f_use != f_use:
        f_use = 0.0
    if f_use < 0.0:
        f_use = 0.0
    if f_use > 1.0:
        f_use = 1.0

    steps = int(L)
    if steps < 0:
        steps = 0
    if steps > 2:
        steps = 2

    stock0 = [0.0 for i in range(m)]
    weights = [0.0 for i in range(m)]
    pipe = [0.0 for j in range(len(pipeline))]

    current_effective = 0.0
    pipeline_total = 0.0

    for i in range(m):
        value = float(age[i])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        stock0[i] = value

        if m == 1:
            weight = W4
        else:
            position = 4.0 * i / (m - 1.0)
            if position <= 1.0:
                weight = W0 + (W1 - W0) * position
            elif position <= 2.0:
                weight = W1 + (W2 - W1) * (position - 1.0)
            elif position <= 3.0:
                weight = W2 + (W3 - W2) * (position - 2.0)
            else:
                weight = W3 + (W4 - W3) * (position - 3.0)

        weights[i] = weight
        current_effective = current_effective + weight * value

    for j in range(len(pipeline)):
        value = float(pipeline[j])
        if value != value or value < 0.0:
            value = 0.0
        if value > 1000000.0:
            value = 1000000.0
        pipe[j] = value
        pipeline_total = pipeline_total + value

    current_effective = current_effective + P * pipeline_total

    shares = [f_use, 1.0 - f_use]
    nodes = [[0.0 for z in range(4)] for h in range(2)]
    variance_scale = (demand_mean * demand_cv) * (demand_mean * demand_cv)

    for h in range(2):
        share = shares[h]
        stream_mean = share * demand_mean

        if stream_mean > 0.0:
            stream_variance = share * variance_scale
            aa = stream_variance / (stream_mean * stream_mean) - 1.0 / stream_mean
            if aa < 1.0:
                aa = 1.0

            root = (aa * aa - 1.0) ** 0.5
            bb = 1.0 + aa + root
            cc = 1.0 + aa - root
            mix_weight = 1.0 / bb
            p1 = 2.0 / (2.0 + stream_mean * bb)
            p2 = 2.0 / (2.0 + stream_mean * cc)
            r1 = 1.0 - p1
            r2 = 1.0 - p2

            masses = [0.0 for z in range(4)]
            moments = [0.0 for z in range(4)]

            for d in range(61):
                probability = mix_weight * p1 * (r1 ** d)
                probability = probability + (1.0 - mix_weight) * p2 * (r2 ** d)
                remaining = probability

                for z in range(4):
                    space = 0.25 - masses[z]
                    if space < 0.0:
                        space = 0.0
                    take = remaining
                    if take > space:
                        take = space
                    if take < 0.0:
                        take = 0.0
                    masses[z] = masses[z] + take
                    moments[z] = moments[z] + take * d
                    remaining = remaining - take
                    if remaining < 0.0:
                        remaining = 0.0

            tail_start = 61.0
            tail_probability1 = r1 ** 61
            tail_probability2 = r2 ** 61
            tail_probability = mix_weight * tail_probability1
            tail_probability = tail_probability + (1.0 - mix_weight) * tail_probability2

            tail_moment1 = tail_probability1 * (tail_start + r1 / p1)
            tail_moment2 = tail_probability2 * (tail_start + r2 / p2)
            tail_moment = mix_weight * tail_moment1
            tail_moment = tail_moment + (1.0 - mix_weight) * tail_moment2

            tail_value = 0.0
            if tail_probability > 0.0:
                tail_value = tail_moment / tail_probability

            remaining = tail_probability
            for z in range(4):
                space = 0.25 - masses[z]
                if space < 0.0:
                    space = 0.0
                take = remaining
                if take > space:
                    take = space
                if take < 0.0:
                    take = 0.0
                masses[z] = masses[z] + take
                moments[z] = moments[z] + take * tail_value
                remaining = remaining - take
                if remaining < 0.0:
                    remaining = 0.0

            for z in range(4):
                if masses[z] > 0.0:
                    nodes[h][z] = moments[z] / masses[z]
                else:
                    nodes[h][z] = stream_mean

    projected_states = [[0.0 for i in range(m)] for t in range(16)]
    projected_effective = [0.0 for t in range(16)]
    alpha_map = [0, 2, 3, 1]

    for t in range(16):
        a_index = t // 4
        b_index = t - 4 * a_index
        c_index = a_index ^ b_index
        d_index = a_index ^ alpha_map[b_index]

        work = [0.0 for i in range(m)]
        for i in range(m):
            work[i] = stock0[i]

        if steps > 0:
            remaining = GF * nodes[0][a_index]
            if remaining < 0.0:
                remaining = 0.0
            for i in range(m):
                take = remaining
                if take > work[i]:
                    take = work[i]
                work[i] = work[i] - take
                remaining = remaining - take
                if remaining < 0.0:
                    remaining = 0.0

            remaining = GL * nodes[1][b_index]
            if remaining < 0.0:
                remaining = 0.0
            for k in range(m):
                i = m - 1 - k
                take = remaining
                if take > work[i]:
                    take = work[i]
                work[i] = work[i] - take
                remaining = remaining - take
                if remaining < 0.0:
                    remaining = 0.0

            for i in range(m - 1):
                work[i] = work[i + 1]
            work[m - 1] = 0.0
            if len(pipe) > 0:
                work[m - 1] = pipe[0]

        if steps > 1:
            remaining = GF * nodes[0][c_index]
            if remaining < 0.0:
                remaining = 0.0
            for i in range(m):
                take = remaining
                if take > work[i]:
                    take = work[i]
                work[i] = work[i] - take
                remaining = remaining - take
                if remaining < 0.0:
                    remaining = 0.0

            remaining = GL * nodes[1][d_index]
            if remaining < 0.0:
                remaining = 0.0
            for k in range(m):
                i = m - 1 - k
                take = remaining
                if take > work[i]:
                    take = work[i]
                work[i] = work[i] - take
                remaining = remaining - take
                if remaining < 0.0:
                    remaining = 0.0

            for i in range(m - 1):
                work[i] = work[i + 1]
            work[m - 1] = 0.0
            if len(pipe) > 1:
                work[m - 1] = pipe[1]

        effective = 0.0
        for i in range(m):
            projected_states[t][i] = work[i]
            effective = effective + weights[i] * work[i]
        projected_effective[t] = effective

    mean_effective = 0.0
    low_effective = projected_effective[0]
    high_effective = projected_effective[0]

    for t in range(16):
        value = projected_effective[t]
        mean_effective = mean_effective + value / 16.0
        if value < low_effective:
            low_effective = value
        if value > high_effective:
            high_effective = value

    quantiles = [0.0, 0.0]
    for r in range(2):
        rank = 8 + r
        low = low_effective
        high = high_effective

        for iteration in range(14):
            midpoint = 0.5 * (low + high)
            count = 0
            for t in range(16):
                if projected_effective[t] <= midpoint:
                    count = count + 1
            if count < rank:
                low = midpoint
            else:
                high = midpoint

        quantiles[r] = 0.5 * (low + high)

    median_effective = 0.5 * (quantiles[0] + quantiles[1])
    base_effective = mean_effective
    base_effective = base_effective + MED * (median_effective - mean_effective)
    base_effective = base_effective + CUR * (current_effective - mean_effective)

    seed = K * (S - base_effective)
    if seed != seed or seed < 0.0:
        seed = 0.0
    if seed > C:
        seed = C

    lifo_share = 1.0 - f_use
    lifo_mean = lifo_share * demand_mean
    lifo_variance = lifo_share * variance_scale
    crowding_risk = 0.0

    if lifo_share > 0.0:
        for t in range(16):
            younger = seed
            path_risk = 0.0

            for k in range(m):
                i = m - 1 - k
                stock = projected_states[t][i]
                lifetime = i + 1.0
                future_mean = lifetime * lifo_mean
                future_variance = lifetime * lifo_variance
                scale = RISK_SCALE * (future_variance ** 0.5) + 1.0
                threshold = younger + 0.5 * stock
                z_value = (threshold - future_mean) / scale
                crowd_probability = 0.5 * (1.0 + z_value / (1.0 + abs(z_value)))
                urgency = (m - i) / float(m)
                path_risk = path_risk + stock * crowd_probability * urgency
                younger = younger + stock

            crowding_risk = crowding_risk + path_risk / 16.0

    effective = base_effective + J * lifo_share * crowding_risk
    q = K * (S - effective)

    if q != q or q < 0.0:
        q = 0.0
    if q > C:
        q = C
    if q > 1000000.0:
        q = 1000000.0
    return q
