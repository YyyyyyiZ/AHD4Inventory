import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 231.46841555901946  # OPT_PARAM: {"initial": 231.46841555901946, "min": 200.0, "max": 400.0, "type": "float"}
    demand_response = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_adjustment = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}
    min_order = 57.622977681992694  # OPT_PARAM: {"initial": 57.622977681992694, "min": 0.0, "max": 100.0, "type": "float"}
    
    target = base_target + demand_response * last_demand
    pipeline_sum = np.sum(pipeline_orders) * pipeline_adjustment
    order_amount = max(min_order, target - on_hand_inventory - pipeline_sum)
    return order_amount
