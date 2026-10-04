import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 153.11235200992093  # OPT_PARAM: {"initial": 153.11235200992093, "min": 150.0, "max": 300.0, "type": "float"}
    demand_response = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 21.95285636183323  # OPT_PARAM: {"initial": 21.95285636183323, "min": 20.0, "max": 100.0, "type": "float"}
    
    smoothed_demand = smoothing_factor * last_demand + (1 - smoothing_factor) * 100.0
    adjusted_target = base_target + demand_response * smoothed_demand + safety_stock
    order_amount = max(0.0, adjusted_target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
