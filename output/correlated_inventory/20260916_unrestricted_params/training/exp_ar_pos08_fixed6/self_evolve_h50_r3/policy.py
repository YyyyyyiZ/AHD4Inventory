import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    target_multiplier = 2.5437981257902518  # OPT_PARAM: {"initial": 2.5437981257902518, "min": 1.0, "max": 3.0, "type": "float"}
    safety_stock = 273.86473078310735  # OPT_PARAM: {"initial": 273.86473078310735, "min": 50.0, "max": 300.0, "type": "float"}
    demand_response_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    
    base_target = target_multiplier * last_demand
    pipeline_total = np.sum(pipeline_orders)
    inventory_position = on_hand_inventory + pipeline_total
    target = base_target + safety_stock
    order_amount = max(0.0, target - inventory_position) * demand_response_factor
    
    return order_amount
