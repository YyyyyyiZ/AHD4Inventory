import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 236.8585620156016  # OPT_PARAM: {"initial": 236.8585620156016, "min": 200.0, "max": 300.0, "type": "float"}
    demand_sensitivity = 1.4  # OPT_PARAM: {"initial": 1.4, "min": 1.0, "max": 1.4, "type": "float"}
    adjustment_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}
    pipeline_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    
    demand_adjustment = demand_sensitivity * last_demand
    target = base_stock + adjustment_factor * (demand_adjustment - base_stock)
    order_amount = max(0.0, target - on_hand_inventory - pipeline_factor * sum(pipeline_orders))
    return order_amount
