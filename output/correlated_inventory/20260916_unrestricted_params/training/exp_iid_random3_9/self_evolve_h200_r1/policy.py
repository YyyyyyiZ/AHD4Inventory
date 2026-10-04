import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    target = 392.82820678467414  # OPT_PARAM: {"initial": 392.82820678467414, "min": 100.0, "max": 500.0, "type": "float"}
    demand_response = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.5, "type": "float"}
    lead_time_adjustment = 2.1854065313448254  # OPT_PARAM: {"initial": 2.1854065313448254, "min": 0.0, "max": 50.0, "type": "float"}
    
    adjusted_target = target + demand_response * last_demand + lead_time_adjustment * (quoted_lead_time - 6)
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, adjusted_target - inventory_position)
    return order_amount
