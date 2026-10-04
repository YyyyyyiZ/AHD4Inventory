import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target_low = 52.54251114369861  # OPT_PARAM: {"initial": 52.54251114369861, "min": 50.0, "max": 150.0, "type": "float"}
    base_target_high = 113.52841221688544  # OPT_PARAM: {"initial": 113.52841221688544, "min": 100.0, "max": 300.0, "type": "float"}
    demand_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    inventory_adjustment = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.5, "type": "float"}
    
    if last_demand >= 100.0 * np.log(2):  # High demand regime
        adjusted_target = base_target_high * demand_multiplier
    else:  # Low demand regime
        adjusted_target = base_target_low
    
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, adjusted_target - inventory_adjustment * inventory_position)
    return order_amount
