import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    target = 226.9270299382197  # OPT_PARAM: {"initial": 226.9270299382197, "min": 100.0, "max": 500.0, "type": "float"}
    order_amount = max(0.0, target - on_hand_inventory - np.sum(pipeline_orders))
    return order_amount
