import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 327.1986177269946  # OPT_PARAM: {"initial": 327.1986177269946, "min": 300.0, "max": 400.0, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_adj = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    safety_stock = 75.78035150730283  # OPT_PARAM: {"initial": 75.78035150730283, "min": 70.0, "max": 120.0, "type": "float"}
    
    demand_component = demand_adjustment * last_demand
    pipeline_component = pipeline_adj * sum(pipeline_orders)
    target = max(base_target, demand_component) + safety_stock
    order_amount = max(0.0, target - on_hand_inventory - pipeline_component)
    return order_amount
