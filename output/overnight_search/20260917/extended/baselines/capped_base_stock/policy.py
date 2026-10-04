def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 12.0 # OPT_PARAM: {"type":"float","initial":12.0,"min":0.0,"max":60.0}
    C = 5.0 # OPT_PARAM: {"type":"float","initial":5.0,"min":0.0,"max":20.0}
    return max(0.0,min(C,S-sum(age)-sum(pipeline)))
