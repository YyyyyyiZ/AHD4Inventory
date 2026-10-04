def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    A = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":8.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    B = 0.75 # OPT_PARAM: {"type":"float","initial":0.75,"min":0.0,"max":1.0}
    H = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":1.0}
    E = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.0}
    K = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.25,"max":2.5}

    m = len(age)
    raw_effective = 0.0
    pipeline_stock = 0.0

    for i in range(m):
        stock = max(0.0, age[i])
        relative_life = (i + 1.0) / max(1.0, float(m))
        raw_effective = raw_effective + stock * (relative_life ** A)

    for j in range(len(pipeline)):
        pipeline_stock = pipeline_stock + max(0.0, pipeline[j])

    raw_effective = raw_effective + P * pipeline_stock

    projected = [0.0] * m
    for i in range(m):
        projected[i] = max(0.0, age[i])

    active = [0.0] * 2
    mix_weight = [0.0] * 2
    ratio1 = [0.0] * 2
    ratio2 = [0.0] * 2

    for stream in range(2):
        if stream == 0:
            group = f
        else:
            group = 1.0 - f

        mean_stream = group * mu
        if mean_stream > 0.0:
            variance_stream = group * (mu * cv) * (mu * cv)
            shape = variance_stream / (mean_stream * mean_stream) - 1.0 / mean_stream
            shape = max(1.0, shape)
            root = max(0.0, shape * shape - 1.0) ** 0.5
            b = 1.0 + shape + root
            c = 1.0 + shape - root
            weight = 1.0 / b
            success1 = 2.0 / (2.0 + mean_stream * b)
            success2 = 2.0 / (2.0 + mean_stream * c)
            active[stream] = 1.0
            mix_weight[stream] = weight
            ratio1[stream] = max(0.0, min(1.0, 1.0 - success1))
            ratio2[stream] = max(0.0, min(1.0, 1.0 - success2))

    projected_effective = 0.0
    forecast_expiry = 0.0
    total_steps = L + m

    for step in range(total_steps):
        for stream in range(2):
            if active[stream] > 0.0:
                weight = mix_weight[stream]
                r1 = ratio1[stream]
                r2 = ratio2[stream]

                available = 0.0
                for i in range(m):
                    available = available + projected[i]

                if available > 0.0:
                    total_n = int(available)
                    total_fraction = available - total_n
                    total_use = 0.0

                    if total_n > 0:
                        total_use = weight * r1 * (1.0 - r1 ** total_n) / max(1.0e-12, 1.0 - r1)
                        total_use = total_use + (1.0 - weight) * r2 * (1.0 - r2 ** total_n) / max(1.0e-12, 1.0 - r2)

                    total_tail = weight * (r1 ** (total_n + 1))
                    total_tail = total_tail + (1.0 - weight) * (r2 ** (total_n + 1))
                    total_use = total_use + total_fraction * total_tail
                    total_use = max(0.0, min(available, total_use))

                    greedy = [0.0] * m
                    exact = [0.0] * m
                    remaining = total_use
                    cumulative = 0.0

                    for pos in range(m):
                        if stream == 0:
                            idx = pos
                        else:
                            idx = m - 1 - pos

                        cohort = projected[idx]
                        take = min(cohort, remaining)
                        greedy[idx] = cohort - take
                        remaining = max(0.0, remaining - take)

                        lower = cumulative
                        upper = cumulative + cohort
                        lower_n = int(lower)
                        upper_n = int(upper)
                        lower_fraction = lower - lower_n
                        upper_fraction = upper - upper_n
                        lower_use = 0.0
                        upper_use = 0.0

                        if lower_n > 0:
                            lower_use = weight * r1 * (1.0 - r1 ** lower_n) / max(1.0e-12, 1.0 - r1)
                            lower_use = lower_use + (1.0 - weight) * r2 * (1.0 - r2 ** lower_n) / max(1.0e-12, 1.0 - r2)

                        lower_tail = weight * (r1 ** (lower_n + 1))
                        lower_tail = lower_tail + (1.0 - weight) * (r2 ** (lower_n + 1))
                        lower_use = lower_use + lower_fraction * lower_tail

                        if upper_n > 0:
                            upper_use = weight * r1 * (1.0 - r1 ** upper_n) / max(1.0e-12, 1.0 - r1)
                            upper_use = upper_use + (1.0 - weight) * r2 * (1.0 - r2 ** upper_n) / max(1.0e-12, 1.0 - r2)

                        upper_tail = weight * (r1 ** (upper_n + 1))
                        upper_tail = upper_tail + (1.0 - weight) * (r2 ** (upper_n + 1))
                        upper_use = upper_use + upper_fraction * upper_tail

                        cohort_use = max(0.0, min(cohort, upper_use - lower_use))
                        exact[idx] = cohort - cohort_use
                        cumulative = upper

                    for i in range(m):
                        projected[i] = max(0.0, (1.0 - H) * greedy[i] + H * exact[i])

        if step >= L and m > 0:
            forecast_expiry = forecast_expiry + max(0.0, projected[0])

        shifted = [0.0] * m
        for i in range(m - 1):
            shifted[i] = projected[i + 1]

        if step < len(pipeline):
            shifted[m - 1] = max(0.0, pipeline[step])

        projected = shifted

        if step + 1 == L:
            projected_effective = 0.0
            for i in range(m):
                relative_life = (i + 1.0) / max(1.0, float(m))
                projected_effective = projected_effective + projected[i] * (relative_life ** A)

    adjusted_projected = max(0.0, projected_effective - E * forecast_expiry)
    effective = (1.0 - B) * raw_effective + B * adjusted_projected
    deficit = max(0.0, S - effective)
    order = min(C, K * deficit)

    if order != order:
        return 0.0
    if order < 0.0:
        return 0.0
    if order > 1.0e12:
        return 1.0e12
    return order
