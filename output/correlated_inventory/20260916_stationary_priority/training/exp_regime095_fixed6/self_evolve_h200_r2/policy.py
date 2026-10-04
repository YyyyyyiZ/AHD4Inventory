import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 80.25667904678812  # OPT_PARAM: {"initial": 80.25667904678812, "min": 50.0, "max": 300.0, "type": "float"}
    demand_response_factor = 0.224543399129966  # OPT_PARAM: {"initial": 0.224543399129966, "min": 0.1, "max": 1.5, "type": "float"}
    inventory_adjustment = 0.8901619584161423  # OPT_PARAM: {"initial": 0.8901619584161423, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_adjustment = 0.35046065309390206  # OPT_PARAM: {"initial": 0.35046065309390206, "min": 0.1, "max": 0.5, "type": "float"}
    
    demand_adjusted = base_target + demand_response_factor * last_demand
    current_position = on_hand_inventory + inventory_adjustment * np.sum(pipeline_orders)
    order_amount = max(0.0, demand_adjusted - pipeline_adjustment * current_position)
    return order_amount
