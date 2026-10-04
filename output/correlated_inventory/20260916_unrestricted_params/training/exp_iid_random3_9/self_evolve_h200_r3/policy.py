import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 324.69989838525777  # OPT_PARAM: {"initial": 324.69989838525777, "min": 250.0, "max": 450.0, "type": "float"}
    lead_time_adjustment = 2.167221915994697  # OPT_PARAM: {"initial": 2.167221915994697, "min": 1.0, "max": 5.0, "type": "float"}
    demand_response = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.1, "type": "float"}
    safety_stock = 54.799898385250515  # OPT_PARAM: {"initial": 54.799898385250515, "min": 50.0, "max": 150.0, "type": "float"}
    
    adjusted_target = base_stock + lead_time_adjustment * quoted_lead_time + safety_stock
    demand_component = demand_response * last_demand
    target = max(adjusted_target, demand_component)
    order_amount = max(0.0, target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
