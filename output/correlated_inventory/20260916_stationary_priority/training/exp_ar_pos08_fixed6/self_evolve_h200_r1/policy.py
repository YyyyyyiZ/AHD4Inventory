import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 183.54452919412546  # OPT_PARAM: {"initial": 183.54452919412546, "min": 50.0, "max": 400.0, "type": "float"}
    demand_response = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    pipeline_adjustment = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    safety_stock = 43.25684640055422  # OPT_PARAM: {"initial": 43.25684640055422, "min": 10.0, "max": 100.0, "type": "float"}
    
    demand_estimate = demand_response * last_demand
    total_pipeline = sum(pipeline_orders)
    target = base_stock + safety_stock + demand_estimate - pipeline_adjustment * total_pipeline
    order_amount = max(0.0, target - on_hand_inventory)
    return order_amount
