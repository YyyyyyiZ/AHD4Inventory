import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 392.1641688051748  # OPT_PARAM: {"initial": 392.1641688051748, "min": 200.0, "max": 400.0, "type": "float"}
    lead_time_adjustment = 2.1584678560750366  # OPT_PARAM: {"initial": 2.1584678560750366, "min": 0.0, "max": 50.0, "type": "float"}
    demand_response_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    
    adjusted_target = base_stock + lead_time_adjustment * (quoted_lead_time - 6)  # Center at mean lead time of 6
    demand_adjusted_target = adjusted_target + demand_response_factor * last_demand  # More responsive to last demand
    
    order_amount = max(0.0, demand_adjusted_target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
