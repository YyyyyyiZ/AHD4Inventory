import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    demand_response_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    pipeline_adjustment = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.0, "max": 0.3, "type": "float"}
    demand_smoothing = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.5, "type": "float"}
    
    smoothed_demand = demand_smoothing * last_demand + (1 - demand_smoothing) * 100.0
    base_target = base_multiplier * smoothed_demand
    dynamic_target = base_target + demand_response_factor * (last_demand - smoothed_demand)
    total_available = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, dynamic_target - pipeline_adjustment * total_available)
    return order_amount
