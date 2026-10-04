import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 316.4914578863064  # OPT_PARAM: {"initial": 316.4914578863064, "min": 100.0, "max": 800.0, "type": "float"}
    safety_stock = 86.49145788630229  # OPT_PARAM: {"initial": 86.49145788630229, "min": 50.0, "max": 400.0, "type": "float"}
    demand_response_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    
    demand_adjustment = demand_response_factor * (last_demand - 100.0)
    target = base_stock + safety_stock + demand_adjustment
    order_amount = max(0.0, target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
