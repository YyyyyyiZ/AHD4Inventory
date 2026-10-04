import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 166.91559478769844  # OPT_PARAM: {"initial": 166.91559478769844, "min": 150.0, "max": 350.0, "type": "float"}
    demand_response = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_adjustment = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20.0, "max": 100.0, "type": "float"}
    
    smoothed_demand = smoothing_factor * last_demand + (1 - smoothing_factor) * 100.0
    demand_estimate = demand_response * smoothed_demand
    pipeline_total = sum(pipeline_orders)
    adjusted_pipeline = pipeline_adjustment * pipeline_total
    target = base_stock + demand_estimate - adjusted_pipeline + safety_stock
    order_amount = max(0.0, target - on_hand_inventory)
    return order_amount
