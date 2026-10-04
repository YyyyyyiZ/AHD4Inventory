import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 160.0410231969247  # OPT_PARAM: {"initial": 160.0410231969247, "min": 100.0, "max": 250.0, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    safety_stock = 60.04102319692182  # OPT_PARAM: {"initial": 60.04102319692182, "min": 30.0, "max": 80.0, "type": "float"}
    demand_response = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    
    adjusted_demand = demand_adjustment * last_demand
    target = base_target + demand_response * adjusted_demand + safety_stock
    order_amount = max(0.0, target - on_hand_inventory - sum(pipeline_orders))
    return order_amount
