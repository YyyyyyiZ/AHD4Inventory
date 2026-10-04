import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 339.84827101001014  # OPT_PARAM: {"initial": 339.84827101001014, "min": 200.0, "max": 500.0, "type": "float"}
    demand_response = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time_adjustment = 2.1783760467133932  # OPT_PARAM: {"initial": 2.1783760467133932, "min": 0.0, "max": 5.0, "type": "float"}
    safety_stock = 39.84827101000799  # OPT_PARAM: {"initial": 39.84827101000799, "min": 0.0, "max": 100.0, "type": "float"}
    
    adjusted_base = base_stock + lead_time_adjustment * quoted_lead_time + safety_stock
    demand_adjusted = last_demand * demand_response
    target = max(adjusted_base, demand_adjusted)
    order_amount = max(0.0, target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
