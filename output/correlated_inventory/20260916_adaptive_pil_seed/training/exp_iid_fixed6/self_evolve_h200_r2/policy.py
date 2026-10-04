import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 1.2118250030649862  # OPT_PARAM: {"initial": 1.2118250030649862, "min": 1.1, "max": 1.4, "type": "float"}
    cap_over_mean = 0.5900111039426388  # OPT_PARAM: {"initial": 0.5900111039426388, "min": 0.5, "max": 0.8, "type": "float"}
    target_forecast_gain = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 1.4, "type": "float"}
    cap_forecast_gain = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.8, "max": 1.0, "type": "float"}
    inventory_gain = 0.6863932058655485  # OPT_PARAM: {"initial": 0.6863932058655485, "min": 0.5, "max": 0.8, "type": "float"}
    demand_response = 0.38205185552456017  # OPT_PARAM: {"initial": 0.38205185552456017, "min": 0.2, "max": 0.5, "type": "float"}
    mean_demand = 100.0
    
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    
    base_target = mean_demand * S_over_mean + target_forecast_gain * (arrival_mean - mean_demand)
    demand_adjusted = base_target + demand_response * (last_demand - mean_demand)
    target = max(0.0, demand_adjusted)
    
    cap = max(0.0, mean_demand * cap_over_mean + cap_forecast_gain * (arrival_mean - mean_demand))
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    
    return order_amount
