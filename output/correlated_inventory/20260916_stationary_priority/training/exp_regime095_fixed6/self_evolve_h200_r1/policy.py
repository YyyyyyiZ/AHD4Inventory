import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock_low = 244.64033037234302  # OPT_PARAM: {"initial": 244.64033037234302, "min": 100.0, "max": 250.0, "type": "float"}
    base_stock_high = 227.69842332107592  # OPT_PARAM: {"initial": 227.69842332107592, "min": 150.0, "max": 350.0, "type": "float"}
    demand_response = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    high_demand_threshold = 100.0 * np.log(2)
    
    if last_demand >= high_demand_threshold:
        target = base_stock_high * (1 + demand_response)
    else:
        target = base_stock_low * (1 - demand_response * 0.5)
    
    order_amount = max(0.0, target - on_hand_inventory - sum(pipeline_orders))
    return order_amount
