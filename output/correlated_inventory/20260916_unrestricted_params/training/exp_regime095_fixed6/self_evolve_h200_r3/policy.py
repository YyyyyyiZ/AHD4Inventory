import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock_high = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400.0, "max": 700.0, "type": "float"}
    base_stock_low = 218.0617096976233  # OPT_PARAM: {"initial": 218.0617096976233, "min": 50.0, "max": 250.0, "type": "float"}
    demand_threshold = 100.0 * np.log(2)
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    demand_response_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    
    if last_demand >= demand_threshold:
        target = base_stock_high
    else:
        target = base_stock_low
    
    target = target + demand_response_factor * (last_demand - 100.0)
    
    projected_inventory = on_hand_inventory + np.sum(pipeline_orders)
    adjusted_target = target * (1 - smoothing_factor) + projected_inventory * smoothing_factor
    
    order_amount = max(0.0, adjusted_target - projected_inventory)
    return order_amount
