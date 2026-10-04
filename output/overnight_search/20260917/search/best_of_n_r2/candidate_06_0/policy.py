def compute_order_amount(age, pipeline, mu, cv, f, L):
    import math

    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":50.0}
    B = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":60.0}
    K_proj = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.5}
    K_ip = 0.25 # OPT_PARAM: {"type":"float","initial":0.25,"min":0.0,"max":1.5}
    old_proj = 0.40 # OPT_PARAM: {"type":"float","initial":0.40,"min":0.0,"max":1.5}
    old_ip = 0.70 # OPT_PARAM: {"type":"float","initial":0.70,"min":0.0,"max":1.5}
    age_power = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.15,"max":4.0}
    pipe_weight = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":1.5}

    m = len(age)
    orig = [0.0] * m
    x = [0.0] * m
    for i in range(m):
        v = float(age[i])
        if not math.isfinite(v) or v < 0.0:
            v = 0.0
        if v > 1000000.0:
            v = 1000000.0
        orig[i] = v
        x[i] = v

    npip = len(pipeline)
    pvec = [0.0] * npip
    for j in range(npip):
        v = float(pipeline[j])
        if not math.isfinite(v) or v < 0.0:
            v = 0.0
        if v > 1000000.0:
            v = 1000000.0
        pvec[j] = v

    mf = float(f) * float(mu)
    vf = float(f) * (float(mu) * float(cv)) ** 2
    if mf > 0.0:
        af = vf / (mf * mf) - 1.0 / mf
        sf = math.sqrt(max(0.0, af * af - 1.0))
        bf = 1.0 + af + sf
        cf = 1.0 + af - sf
        fw = 1.0 / bf
        fp1 = 2.0 / (2.0 + mf * bf)
        fp2 = 2.0 / (2.0 + mf * cf)
        fr1 = 1.0 - fp1
        fr2 = 1.0 - fp2
    else:
        fw = 0.0
        fr1 = 0.0
        fr2 = 0.0

    gl = 1.0 - float(f)
    ml = gl * float(mu)
    vl = gl * (float(mu) * float(cv)) ** 2
    if ml > 0.0:
        al = vl / (ml * ml) - 1.0 / ml
        sl = math.sqrt(max(0.0, al * al - 1.0))
        bl = 1.0 + al + sl
        cl = 1.0 + al - sl
        lw = 1.0 / bl
        lp1 = 2.0 / (2.0 + ml * bl)
        lp2 = 2.0 / (2.0 + ml * cl)
        lr1 = 1.0 - lp1
        lr2 = 1.0 - lp2
    else:
        lw = 0.0
        lr1 = 0.0
        lr2 = 0.0

    lead = int(L)
    if lead < 0:
        lead = 0

    for step in range(lead):
        total = 0.0
        for i in range(m):
            total = total + x[i]

        survivor = [0.0] * m
        if total > 0.0:
            left = 0.0
            for i in range(m):
                amount = x[i]
                if amount > 0.0:
                    pieces = int(math.ceil(amount))
                    if pieces < 1:
                        pieces = 1
                    if pieces > 96:
                        pieces = 96
                    width = amount / float(pieces)
                    remaining = 0.0

                    for z in range(pieces):
                        position = left + (float(z) + 0.5) * width
                        above = total - position

                        if mf <= 0.0:
                            fifo_survival = 1.0
                        else:
                            ef = int(math.ceil(position))
                            fifo_survival = 1.0 - fw * (fr1 ** ef) - (1.0 - fw) * (fr2 ** ef)
                            if fifo_survival < 0.0:
                                fifo_survival = 0.0
                            if fifo_survival > 1.0:
                                fifo_survival = 1.0

                        if ml <= 0.0:
                            lifo_survival = 1.0
                        else:
                            el = int(math.ceil(above))
                            lifo_survival = 1.0 - lw * (lr1 ** el) - (1.0 - lw) * (lr2 ** el)
                            if lifo_survival < 0.0:
                                lifo_survival = 0.0
                            if lifo_survival > 1.0:
                                lifo_survival = 1.0

                        remaining = remaining + width * fifo_survival * lifo_survival

                    survivor[i] = remaining
                left = left + amount

        nxt = [0.0] * m
        for i in range(m - 1):
            nxt[i] = survivor[i + 1]

        if step < lead - 1 and step < npip:
            nxt[m - 1] = pvec[step]
        else:
            nxt[m - 1] = 0.0
        x = nxt

    projected_effective = 0.0
    current_effective = 0.0
    if m > 0:
        for i in range(m):
            relative_age = float(i + 1) / float(m)
            shape = relative_age ** age_power
            wp = old_proj + (1.0 - old_proj) * shape
            wi = old_ip + (1.0 - old_ip) * shape
            projected_effective = projected_effective + wp * x[i]
            current_effective = current_effective + wi * orig[i]

    pipeline_total = 0.0
    for j in range(npip):
        pipeline_total = pipeline_total + pvec[j]
    current_effective = current_effective + pipe_weight * pipeline_total

    projected_gap = S - projected_effective
    if projected_gap < 0.0:
        projected_gap = 0.0

    ip_gap = B - current_effective
    if ip_gap < 0.0:
        ip_gap = 0.0

    order = K_proj * projected_gap + K_ip * ip_gap
    if not math.isfinite(order) or order < 0.0:
        return 0.0
    return float(order)
