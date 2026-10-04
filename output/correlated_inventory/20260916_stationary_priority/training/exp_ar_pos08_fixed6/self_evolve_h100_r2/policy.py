import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 172.40214921821476  # OPT_PARAM: {"initial": 172.40214921821476, "min": 50.0, "max": 300.0, "type": "float"}
    demand_response = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    safety_stock = 62.402149218211036  # OPT_PARAM: {"initial": 62.402149218211036, "min": 10.0, "max": 100.0, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    smoothed_target = smoothing_factor * adjusted_target + (1 - smoothing_factor) * base_target
    target = smoothed_target + safety_stock
    order_amount = max(0.0, target - on_hand_inventory - sum(pipeline_orders))
    return order_amount
