import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 66.89007496154362  # OPT_PARAM: {"initial": 66.89007496154362, "min": 50.0, "max": 200.0, "type": "float"}
    demand_sensitivity = 0.01305846762966893  # OPT_PARAM: {"initial": 0.01305846762966893, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_sensitivity = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    
    # Adjust target based on last demand (mean-reverting behavior)
    adjusted_target = base_target + demand_sensitivity * (100.0 - last_demand)
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, adjusted_target - pipeline_sensitivity * inventory_position)
    return order_amount
