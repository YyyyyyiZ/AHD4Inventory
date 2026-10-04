def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":60.0}
    DMEAN = 0.85 # OPT_PARAM: {"type":"float","initial":0.85,"min":0.2,"max":1.8}
    DCV = 0.0 # OPT_PARAM: {"type":"float","initial":0.0,"min":-0.5,"max":0.5}
    KFIFO = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    KLIFO = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    CPROJECTED = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":2.0}
    KSHORT = 0.5 # OPT_PARAM: {"type":"float","initial":0.5,"min":0.0,"max":2.0}
    KEXPIRY = 0.2 # OPT_PARAM: {"type":"float","initial":0.2,"min":0.0,"max":2.0}
    m = len(age)
    total_age = 0.0
    old_stock = 0.0
    young_stock = 0.0
    i = 0
    for i in range(m):
        x = float(age[i])
        total_age = total_age + x
        if i + 1 <= L:
            old_stock = old_stock + x
        else:
            young_stock = young_stock + x
    pipe_total = 0.0
    j = 0
    for j in range(len(pipeline)):
        pipe_total = pipe_total + float(pipeline[j])
    forecast_factor = DMEAN + DCV * cv
    if forecast_factor < 0.0:
        forecast_factor = 0.0
    lead_demand = mu * float(L) * forecast_factor
    fifo_pressure = KFIFO * f * lead_demand
    lifo_demand = KLIFO * (1.0 - f) * lead_demand
    lifo_reach = lifo_demand - young_stock - pipe_total
    if lifo_reach < 0.0:
        lifo_reach = 0.0
    old_service = fifo_pressure + lifo_reach
    if old_service > old_stock:
        old_service = old_stock
    expected_expiry = old_stock - old_service
    available_at_lead = total_age + pipe_total - expected_expiry
    projected_stock = available_at_lead - lead_demand
    if projected_stock < 0.0:
        projected_stock = 0.0
    projected_shortage = lead_demand - available_at_lead
    if projected_shortage < 0.0:
        projected_shortage = 0.0
    q = S - CPROJECTED * projected_stock + KSHORT * projected_shortage + KEXPIRY * expected_expiry
    if q != q:
        q = 0.0
    if q < 0.0:
        q = 0.0
    if q > 1000000.0:
        q = 1000000.0
    return float(q)
