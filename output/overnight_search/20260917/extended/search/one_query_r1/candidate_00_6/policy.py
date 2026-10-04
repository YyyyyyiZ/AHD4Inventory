def compute_order_amount(age, pipeline, mu, cv, f, L):
    Q = 4.0 # OPT_PARAM: {"type":"float","initial":4.0,"min":0.0,"max":20.0}
    S = 15.0 # OPT_PARAM: {"type":"float","initial":15.0,"min":0.0,"max":60.0}
    C = 25.0 # OPT_PARAM: {"type":"float","initial":25.0,"min":0.0,"max":60.0}
    KU = 0.8 # OPT_PARAM: {"type":"float","initial":0.8,"min":0.0,"max":3.0}
    KD = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":3.0}
    KE = 0.6 # OPT_PARAM: {"type":"float","initial":0.6,"min":0.0,"max":3.0}
    T = 2.0 # OPT_PARAM: {"type":"float","initial":2.0,"min":0.0,"max":30.0}
    KY = 0.15 # OPT_PARAM: {"type":"float","initial":0.15,"min":0.0,"max":2.0}
    Y = 8.0 # OPT_PARAM: {"type":"float","initial":8.0,"min":0.0,"max":40.0}
    WP = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    m = len(age)
    stock = 0.0
    pressure = 0.0
    fresh = 0.0
    for i in range(m):
        x = (i + 1.0) / m
        stock = stock + age[i]
        pressure = pressure + age[i] * (1.0 - x)
        fresh = fresh + age[i] * x
    pipe = 0.0
    for j in range(len(pipeline)):
        pipe = pipe + pipeline[j]
    position = stock + WP * pipe
    shortage_signal = max(0.0, S - position)
    excess_signal = max(0.0, position - S)
    expiry_signal = max(0.0, pressure - T)
    fresh_signal = max(0.0, fresh + pipe - Y)
    raw = Q + KU * shortage_signal - KD * excess_signal + KE * expiry_signal - KY * fresh_signal
    return max(0.0, min(C, raw))
