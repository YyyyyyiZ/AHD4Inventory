import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_multiplier = 3.0670569407555943  # OPT_PARAM: {"initial": 3.0670569407555943, "min": 3.0, "max": 3.5, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.2, "type": "float"}
    min_buffer = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 90.0, "max": 100.0, "type": "float"}
    demand_response = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.5, "type": "float"}
    
    smoothed_demand = smoothing_factor * last_demand + (1 - smoothing_factor) * 100.0
    target = max(min_buffer, base_multiplier * smoothed_demand)
    order_amount = max(0.0, demand_response * (target - on_hand_inventory - sum(pipeline_orders)))
    return order_amount
