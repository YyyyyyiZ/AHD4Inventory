import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 402.98258104331575  # OPT_PARAM: {"initial": 402.98258104331575, "min": 350.0, "max": 600.0, "type": "float"}
    demand_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.2, "type": "float"}
    
    adjusted_target = base_stock + demand_factor * last_demand
    smoothed_target = smoothing_factor * adjusted_target + (1 - smoothing_factor) * base_stock
    order_amount = max(0.0, smoothed_target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
