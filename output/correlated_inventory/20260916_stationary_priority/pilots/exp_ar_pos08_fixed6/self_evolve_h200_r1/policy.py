import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    target_ratio = 0.8165334102457291  # OPT_PARAM: {"initial": 0.8165334102457291, "min": 0.5, "max": 3.0, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 10.0, "max": 150.0, "type": "float"}
    pipeline_adjustment = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    
    smoothed_demand = demand_smoothing * last_demand + (1 - demand_smoothing) * 100.0
    target_inventory = target_ratio * smoothed_demand + safety_stock
    pipeline_contrib = pipeline_adjustment * sum(pipeline_orders[:quoted_lead_time])
    order_amount = max(0.0, target_inventory - on_hand_inventory - pipeline_contrib)
    return order_amount
