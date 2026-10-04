import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 0.5443961102339673  # OPT_PARAM: {"initial": 0.5443961102339673, "min": 0.0, "max": 3.0, "type": "float"}
    cap_over_mean = 4.5  # OPT_PARAM: {"initial": 4.5, "min": 0.0, "max": 12.0, "type": "float"}
    target_forecast_gain = 0.7437695186068028  # OPT_PARAM: {"initial": 0.7437695186068028, "min": -1.0, "max": 3.0, "type": "float"}
    cap_forecast_gain = 5.1  # OPT_PARAM: {"initial": 5.1, "min": -1.0, "max": 15.0, "type": "float"}
    inventory_gain = 0.9841852453917584  # OPT_PARAM: {"initial": 0.9841852453917584, "min": 0.0, "max": 2.0, "type": "float"}
    last_demand_factor = 0.2848166909034908  # OPT_PARAM: {"initial": 0.2848166909034908, "min": 0.0, "max": 1.0, "type": "float"}
    
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    
    # Blend between mean demand and last demand to be more responsive
    adjusted_mean = mean_demand * (1 - last_demand_factor) + last_demand * last_demand_factor
    
    target = max(0.0, adjusted_mean * S_over_mean + target_forecast_gain * (arrival_mean - adjusted_mean))
    cap = max(0.0, adjusted_mean * cap_over_mean + cap_forecast_gain * (arrival_mean - adjusted_mean))
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory))
    
    return order_amount
