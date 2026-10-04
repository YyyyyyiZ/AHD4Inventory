import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 128.42862990607142  # OPT_PARAM: {"initial": 128.42862990607142, "min": 50.0, "max": 300.0, "type": "float"}
    demand_multiplier = 0.6311160847183058  # OPT_PARAM: {"initial": 0.6311160847183058, "min": 0.5, "max": 2.5, "type": "float"}
    smooth_factor = 0.2939568621453809  # OPT_PARAM: {"initial": 0.2939568621453809, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_adjustment = 0.7548462798322613  # OPT_PARAM: {"initial": 0.7548462798322613, "min": 0.1, "max": 1.0, "type": "float"}
    
    adjusted_target = base_target + demand_multiplier * last_demand
    smoothed_target = smooth_factor * adjusted_target + (1 - smooth_factor) * (on_hand_inventory + sum(pipeline_orders))
    order_amount = max(0.0, smoothed_target - pipeline_adjustment * sum(pipeline_orders) - on_hand_inventory)
    return order_amount
