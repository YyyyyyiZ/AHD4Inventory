import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 1114.0291991131562  # OPT_PARAM: {"initial": 1114.0291991131562, "min": 800.0, "max": 1200.0, "type": "float"}
    demand_sensitivity = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    
    demand_adjusted = base_stock + demand_sensitivity * (last_demand - 100.0)
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, adjustment_factor * (demand_adjusted - inventory_position))
    return order_amount
