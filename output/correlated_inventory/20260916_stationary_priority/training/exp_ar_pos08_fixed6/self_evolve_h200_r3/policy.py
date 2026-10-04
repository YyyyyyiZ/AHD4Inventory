import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 226.7667443273936  # OPT_PARAM: {"initial": 226.7667443273936, "min": 100.0, "max": 500.0, "type": "float"}
    demand_response = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    min_order = 0.6840888067051129  # OPT_PARAM: {"initial": 0.6840888067051129, "min": 0.0, "max": 20.0, "type": "float"}
    pipeline_coverage = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    order_amount = max(min_order, adjusted_target - on_hand_inventory - pipeline_coverage * sum(pipeline_orders))
    return order_amount
