import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 188.1393579754419  # OPT_PARAM: {"initial": 188.1393579754419, "min": 150.0, "max": 300.0, "type": "float"}
    demand_response = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lead_time_adjustment = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.1, "type": "float"}
    min_order = 49.632635501119935  # OPT_PARAM: {"initial": 49.632635501119935, "min": 0.0, "max": 50.0, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand + lead_time_adjustment * quoted_lead_time * base_target
    net_inventory = on_hand_inventory + np.sum(pipeline_orders)
    order_amount = max(min_order, adjusted_target - net_inventory)
    return max(0.0, order_amount)
