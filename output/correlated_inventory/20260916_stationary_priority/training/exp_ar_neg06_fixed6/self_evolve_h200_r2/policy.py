import numpy as np
import math

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 482.4950326374659  # OPT_PARAM: {"initial": 482.4950326374659, "min": 400.0, "max": 500.0, "type": "float"}
    demand_response_factor = 0.48394596691047015  # OPT_PARAM: {"initial": 0.48394596691047015, "min": 0.1, "max": 0.5, "type": "float"}
    min_target = 150.1  # OPT_PARAM: {"initial": 150.1, "min": 120.0, "max": 180.0, "type": "float"}
    demand_smoothing = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    
    expected_demand = max(40.0, min(200.0, 100.0 + demand_smoothing * (100.0 - last_demand)))
    adjusted_target = base_target + demand_response_factor * (expected_demand - 100.0)
    target = max(min_target, adjusted_target)
    
    order_amount = max(0.0, target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
