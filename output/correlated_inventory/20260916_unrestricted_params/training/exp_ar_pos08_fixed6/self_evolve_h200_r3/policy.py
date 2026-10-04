import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 249.24384544928617  # OPT_PARAM: {"initial": 249.24384544928617, "min": 50.0, "max": 300.0, "type": "float"}
    demand_response = 0.7652173631537639  # OPT_PARAM: {"initial": 0.7652173631537639, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.2646042201299269  # OPT_PARAM: {"initial": 0.2646042201299269, "min": 0.1, "max": 0.9, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, smoothing_factor * (adjusted_target - inventory_position))
    return order_amount
