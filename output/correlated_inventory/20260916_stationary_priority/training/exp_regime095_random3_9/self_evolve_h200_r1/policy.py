import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 259.11107797698776  # OPT_PARAM: {"initial": 259.11107797698776, "min": 250.0, "max": 500.0, "type": "float"}
    demand_multiplier = 3.790424124191899  # OPT_PARAM: {"initial": 3.790424124191899, "min": 2.0, "max": 4.0, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 10.0, "type": "float"}
    
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    demand_component = demand_multiplier * last_demand
    target = min(base_target + demand_component, 1000.0)
    order_amount = max(min_order, pipeline_weight * (target - inventory_position))
    return order_amount
