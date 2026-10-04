import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 312.812785136335  # OPT_PARAM: {"initial": 312.812785136335, "min": 200.0, "max": 400.0, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    lead_time_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    min_order = 48.28926998671006  # OPT_PARAM: {"initial": 48.28926998671006, "min": 0.0, "max": 50.0, "type": "float"}
    
    dynamic_target = base_target * (1 + (quoted_lead_time - 6) / 6 * lead_time_factor)
    adjusted_last_demand = last_demand * demand_adjustment
    target = max(dynamic_target, adjusted_last_demand)
    order_amount = max(min_order, target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
