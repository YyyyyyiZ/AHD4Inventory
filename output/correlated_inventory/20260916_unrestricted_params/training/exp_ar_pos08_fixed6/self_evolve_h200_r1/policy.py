import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 187.29136256585102  # OPT_PARAM: {"initial": 187.29136256585102, "min": 150.0, "max": 350.0, "type": "float"}
    demand_response = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    
    smoothed_demand = demand_smoothing * last_demand + (1 - demand_smoothing) * 100.0
    adjusted_target = base_stock + demand_response * smoothed_demand
    pipeline_adjustment = pipeline_weight * np.sum(pipeline_orders)
    order_amount = max(0.0, adjusted_target - on_hand_inventory - np.sum(pipeline_orders) + pipeline_adjustment)
    return order_amount
