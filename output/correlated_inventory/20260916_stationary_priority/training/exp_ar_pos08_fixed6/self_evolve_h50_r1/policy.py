import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 117.53287059636646  # OPT_PARAM: {"initial": 117.53287059636646, "min": 50.0, "max": 200.0, "type": "float"}
    demand_response = 0.16091018470609797  # OPT_PARAM: {"initial": 0.16091018470609797, "min": 0.1, "max": 1.5, "type": "float"}
    inventory_coverage = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.0, "type": "float"}
    pipeline_coverage = 0.47012324492030344  # OPT_PARAM: {"initial": 0.47012324492030344, "min": 0.1, "max": 1.5, "type": "float"}
    
    adjusted_target = base_target + demand_response * last_demand
    total_coverage = on_hand_inventory * inventory_coverage + np.sum(pipeline_orders) * pipeline_coverage
    order_amount = max(0.0, adjusted_target - total_coverage)
    return order_amount
