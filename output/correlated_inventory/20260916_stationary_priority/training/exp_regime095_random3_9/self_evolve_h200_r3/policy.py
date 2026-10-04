import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 109.33740256643024  # OPT_PARAM: {"initial": 109.33740256643024, "min": 100, "max": 150, "type": "float"}
    high_target_multiplier = 1.926176108969146  # OPT_PARAM: {"initial": 1.926176108969146, "min": 1.8, "max": 2.2, "type": "float"}
    pipeline_weight = 0.4881418258499627  # OPT_PARAM: {"initial": 0.4881418258499627, "min": 0.3, "max": 0.5, "type": "float"}
    demand_response = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    
    if last_demand >= 100.0 * np.log(2):
        target = base_target * high_target_multiplier
    else:
        target = base_target
    
    recent_demand_adjustment = demand_response * last_demand
    adjusted_target = max(target, recent_demand_adjustment)
    order_amount = max(0.0, adjusted_target - on_hand_inventory - pipeline_weight * sum(pipeline_orders))
    return order_amount
