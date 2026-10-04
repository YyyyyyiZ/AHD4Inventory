import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    demand_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    base_target = 235.4236435888763  # OPT_PARAM: {"initial": 235.4236435888763, "min": 50.0, "max": 500.0, "type": "float"}
    demand_response = 0.1581497372162566  # OPT_PARAM: {"initial": 0.1581497372162566, "min": 0.1, "max": 2.0, "type": "float"}
    
    predicted_demand = demand_weight * last_demand + (1 - demand_weight) * 100.0
    target = base_target + demand_response * max(0, predicted_demand - 100.0)
    order_amount = max(0.0, target - on_hand_inventory - sum(pipeline_orders))
    return order_amount
