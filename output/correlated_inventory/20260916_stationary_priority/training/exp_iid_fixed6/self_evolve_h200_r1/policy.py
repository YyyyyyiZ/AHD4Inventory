import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 271.1603356827065  # OPT_PARAM: {"initial": 271.1603356827065, "min": 200.0, "max": 400.0, "type": "float"}
    demand_sensitivity = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.8, "type": "float"}
    inventory_sensitivity = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_adjustment = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.2, "type": "float"}
    
    adjusted_target = base_stock + demand_sensitivity * last_demand
    pipeline_sum = pipeline_adjustment * np.sum(pipeline_orders)
    effective_inventory = on_hand_inventory + pipeline_sum
    order_amount = max(0.0, adjusted_target - inventory_sensitivity * effective_inventory)
    return order_amount
