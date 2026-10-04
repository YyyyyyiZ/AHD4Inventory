import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 161.9628774535099  # OPT_PARAM: {"initial": 161.9628774535099, "min": 150.0, "max": 250.0, "type": "float"}
    demand_response = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    pipeline_coef = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    min_order = 66.99396590225446  # OPT_PARAM: {"initial": 66.99396590225446, "min": 50.0, "max": 100.0, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    inventory_position = on_hand_inventory + pipeline_coef * sum(pipeline_orders)
    order_amount = max(min_order, adjusted_target - inventory_position)
    return order_amount
