def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 10.0 # OPT_PARAM: {"type":"float","initial":10.0,"min":0.0,"max":60.0}
    C = 6.0 # OPT_PARAM: {"type":"float","initial":6.0,"min":0.0,"max":30.0}
    a = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    effective = 0.0
    for i in range(len(age)):
        effective = effective + age[i]*min(1.0,((i+1.0)/len(age))**a)
    return max(0.0,min(C,S-effective-sum(pipeline)))
