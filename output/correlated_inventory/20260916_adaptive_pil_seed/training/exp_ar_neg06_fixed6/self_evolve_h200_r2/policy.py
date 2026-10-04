import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 1.0013206381044208  # OPT_PARAM: {"initial": 1.0013206381044208, "min": 0.8, "max": 1.3, "type": "float"}
    cap_over_mean = 0.7322393047411019  # OPT_PARAM: {"initial": 0.7322393047411019, "min": 0.7, "max": 1.2, "type": "float"}
    target_forecast_gain = 1.897407109391926  # OPT_PARAM: {"initial": 1.897407109391926, "min": 0.5, "max": 2.0, "type": "float"}
    cap_forecast_gain = 0.5  # OPT_PARAM: {"initial": 0.5, "min": -0.5, "max": 0.5, "type": "float"}
    inventory_gain = 0.9401124098252348  # OPT_PARAM: {"initial": 0.9401124098252348, "min": 0.5, "max": 1.0, "type": "float"}
    last_demand_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    
    # Blend standard mean with last demand observation
    adjusted_mean = (1 - last_demand_weight) * mean_demand + last_demand_weight * last_demand
    target = max(0.0, adjusted_mean * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand))
    cap = max(0.0, adjusted_mean * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))
    
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    return order_amount
