import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 172.97241406327208  # OPT_PARAM: {"initial": 172.97241406327208, "min": 100.0, "max": 300.0, "type": "float"}
    demand_response = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 93.10562735142612  # OPT_PARAM: {"initial": 93.10562735142612, "min": 80.0, "max": 200.0, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    smoothed_target = smoothing_factor * adjusted_target + (1 - smoothing_factor) * (on_hand_inventory + sum(pipeline_orders))
    order_amount = max(0.0, smoothed_target + safety_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
