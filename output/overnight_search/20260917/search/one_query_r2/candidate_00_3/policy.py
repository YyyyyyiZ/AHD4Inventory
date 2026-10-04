def compute_order_amount(age, pipeline, mu, cv, f, L):
    R = 4.0 # OPT_PARAM: {"type":"float","initial":4.0,"min":0.0,"max":15.0}
    TPOSITION = 20.0 # OPT_PARAM: {"type":"float","initial":20.0,"min":0.0,"max":60.0}
    TSURVIVE = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":50.0}
    TYOUNG = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":40.0}
    KPOSITION = 0.4 # OPT_PARAM: {"type":"float","initial":0.4,"min":0.0,"max":2.0}
    KSURVIVE = 0.3 # OPT_PARAM: {"type":"float","initial":0.3,"min":0.0,"max":2.0}
    KYOUNG = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.0}
    KEXPIRY = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":2.0}
    m = len(age)
    total_age = 0.0
    old_stock = 0.0
    survivor_stock = 0.0
    youngest_stock = 0.0
    i = 0
    for i in range(m):
        x = float(age[i])
        total_age = total_age + x
        if i + 1 <= L:
            old_stock = old_stock + x
        if i + 1 > L:
            survivor_stock = survivor_stock + x
        if i + 1 > L + 1:
            youngest_stock = youngest_stock + x
    pipe_total = 0.0
    j = 0
    for j in range(len(pipeline)):
        pipe_total = pipe_total + float(pipeline[j])
    inventory_position = total_age + pipe_total
    survivor_echelon = survivor_stock + pipe_total
    young_echelon = youngest_stock + pipe_total
    gap_position = TPOSITION - inventory_position
    gap_survive = TSURVIVE - survivor_echelon
    gap_young = TYOUNG - young_echelon
    if gap_survive < 0.0:
        gap_survive = 0.0
    if gap_young < 0.0:
        gap_young = 0.0
    fifo_old_service = float(L) * f * mu
    lifo_excess = float(L) * (1.0 - f) * mu - survivor_stock - pipe_total
    if lifo_excess < 0.0:
        lifo_excess = 0.0
    old_service = fifo_old_service + lifo_excess
    expiry_risk = old_stock - old_service
    if expiry_risk < 0.0:
        expiry_risk = 0.0
    q = R + KPOSITION * gap_position + KSURVIVE * gap_survive + KYOUNG * gap_young - KEXPIRY * expiry_risk
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
