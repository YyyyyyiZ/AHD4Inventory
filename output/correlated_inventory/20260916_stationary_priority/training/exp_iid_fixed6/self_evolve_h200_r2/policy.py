import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 294.797001035174  # OPT_PARAM: {"initial": 294.797001035174, "min": 100.0, "max": 600.0, "type": "float"}
    demand_response = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 2.0, "type": "float"}
    safety_stock = 94.79700103467039  # OPT_PARAM: {"initial": 94.79700103467039, "min": 50.0, "max": 300.0, "type": "float"}
    min_order = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0.0, "max": 50.0, "type": "float"}
    
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    adjusted_base = base_stock + safety_stock + demand_response * (last_demand - 100.0)
    order_amount = max(min_order, adjusted_base - inventory_position)
    return order_amount
