import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 61.00926882074305  # OPT_PARAM: {"initial": 61.00926882074305, "min": 50.0, "max": 120.0, "type": "float"}
    demand_response = 0.15049617067344262  # OPT_PARAM: {"initial": 0.15049617067344262, "min": 0.1, "max": 0.4, "type": "float"}
    inventory_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.5, "type": "float"}
    pipeline_weight = 0.18961198282493966  # OPT_PARAM: {"initial": 0.18961198282493966, "min": 0.1, "max": 0.3, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    order_amount = max(0.0, adjusted_target - inventory_weight * on_hand_inventory - pipeline_weight * sum(pipeline_orders))
    return order_amount
