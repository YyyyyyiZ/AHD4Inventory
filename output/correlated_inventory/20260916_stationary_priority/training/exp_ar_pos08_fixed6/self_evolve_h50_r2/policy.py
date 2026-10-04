import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 119.05585804725955  # OPT_PARAM: {"initial": 119.05585804725955, "min": 100.0, "max": 300.0, "type": "float"}
    demand_response_factor = 0.40753594728924275  # OPT_PARAM: {"initial": 0.40753594728924275, "min": 0.3, "max": 1.0, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20.0, "max": 100.0, "type": "float"}
    min_order = 18.807511639614592  # OPT_PARAM: {"initial": 18.807511639614592, "min": 0.0, "max": 30.0, "type": "float"}
    
    target = base_target + demand_response_factor * last_demand
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(min_order, target - net_inventory + safety_stock)
    return order_amount
