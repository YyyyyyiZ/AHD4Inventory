def compute_order_amount(age, pipeline, mu, cv, f, L):
    total_target = 16.0 # OPT_PARAM: {"type":"float","initial":16.0,"min":0.0,"max":60.0}
    young_target = 13.0 # OPT_PARAM: {"type":"float","initial":13.0,"min":0.0,"max":60.0}
    C = 24.0 # OPT_PARAM: {"type":"float","initial":24.0,"min":0.0,"max":60.0}
    young_power = 1.2 # OPT_PARAM: {"type":"float","initial":1.2,"min":0.1,"max":6.0}
    total_pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    young_pipeline_credit = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    fifo_scale = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.0,"max":4.0}
    m = len(age)
    total = 0.0
    young_equivalent = 0.0
    for i in range(m):
        total = total + age[i]
        x = (i + 1.0) / m
        young_equivalent = young_equivalent + age[i] * (x ** young_power)
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    total_signal = total_target - total - total_pipeline_credit * pipe
    young_signal = young_target - young_equivalent - young_pipeline_credit * pipe
    fifo_signal = fifo_scale * f * young_signal
    raw = max(total_signal, fifo_signal)
    return max(0.0, min(C, raw))
