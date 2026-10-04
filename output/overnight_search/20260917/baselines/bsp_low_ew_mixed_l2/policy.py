def compute_order_amount(age, pipeline, mu, cv, f, L):
    S1 = 8.0 # OPT_PARAM: {"type":"float","initial":8.0,"min":0.0,"max":60.0}
    S2 = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    b = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.25,"max":60.0}
    onhand = sum(age)
    ip = onhand + sum(pipeline)
    fifo = f*mu
    after_demand = max(0.0,onhand-mu)
    waste0 = min(max(0.0,age[0]-fifo),after_demand)
    next_oldest = min(max(0.0,age[0]+age[1]-fifo),after_demand)-waste0
    next_onhand = after_demand-waste0+pipeline[0]
    waste1 = min(max(0.0,next_oldest-fifo),max(0.0,next_onhand-mu))
    ew = waste0+waste1
    alpha = 1.0-(S2-S1)/b
    if ip < b:
        return max(0.0,S1-alpha*ip+ew)
    return max(0.0,S2-ip+ew)
