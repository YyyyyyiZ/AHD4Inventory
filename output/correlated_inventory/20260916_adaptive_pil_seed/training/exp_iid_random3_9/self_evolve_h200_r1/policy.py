import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 0.911442502462386  # OPT_PARAM: {"initial": 0.911442502462386, "min": 0.5, "max": 2.0, "type": "float"}
    cap_over_mean = 0.8464285272209195  # OPT_PARAM: {"initial": 0.8464285272209195, "min": 0.5, "max": 2.0, "type": "float"}
    target_forecast_gain = 0.35  # OPT_PARAM: {"initial": 0.35, "min": 0.0, "max": 1.0, "type": "float"}
    cap_forecast_gain = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.0, "max": 1.0, "type": "float"}
    inventory_gain = 0.7766929175352952  # OPT_PARAM: {"initial": 0.7766929175352952, "min": 0.5, "max": 1.5, "type": "float"}
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    target = max(0.0, mean_demand * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand))
    cap = max(0.0, mean_demand * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    return order_amount
