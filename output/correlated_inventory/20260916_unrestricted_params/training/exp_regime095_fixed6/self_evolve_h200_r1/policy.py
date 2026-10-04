import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock_min = 219.6053865825864  # OPT_PARAM: {"initial": 219.6053865825864, "min": 180.0, "max": 250.0, "type": "float"}
    base_stock_max = 463.5221462621035  # OPT_PARAM: {"initial": 463.5221462621035, "min": 400.0, "max": 500.0, "type": "float"}
    demand_sensitivity = 1.2499962340784292  # OPT_PARAM: {"initial": 1.2499962340784292, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.4, "type": "float"}
    demand_threshold = 100.0 * np.log(2)
    
    if last_demand >= demand_threshold:
        base_stock = base_stock_max
    else:
        base_stock = base_stock_min
        
    current_position = on_hand_inventory + np.sum(pipeline_orders)
    order_amount = max(0.0, smoothing_factor * (demand_sensitivity * base_stock - current_position))
    
    return order_amount
