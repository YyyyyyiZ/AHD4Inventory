import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    S_over_mean = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    cap_over_mean = 3.5  # OPT_PARAM: {"initial": 3.5, "min": 2.5, "max": 4.0, "type": "float"}
    target_forecast_gain = 1.2566730385508063  # OPT_PARAM: {"initial": 1.2566730385508063, "min": 0.9, "max": 1.3, "type": "float"}
    cap_forecast_gain = 2.3  # OPT_PARAM: {"initial": 2.3, "min": 2.0, "max": 2.5, "type": "float"}
    inventory_gain = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.8, "type": "float"}
    demand_response = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.2, "type": "float"}
    high_regime_adjustment = 1.278660344164842  # OPT_PARAM: {"initial": 1.278660344164842, "min": 1.2, "max": 1.8, "type": "float"}
    low_regime_adjustment = 0.7340128158737399  # OPT_PARAM: {"initial": 0.7340128158737399, "min": 0.7, "max": 1.1, "type": "float"}
    pipeline_adjustment = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.3, "type": "float"}
    
    mean_demand = 100.0
    arrival_mean = conditional_arrival_mean(last_demand, quoted_lead_time)
    projected_inventory = conditional_projected_inventory(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time)
    total_pipeline = np.sum(pipeline_orders)
    
    if last_demand >= 100.0 * np.log(2):
        adjusted_mean = high_regime_adjustment * ((1 - demand_response) * mean_demand + demand_response * last_demand)
    else:
        adjusted_mean = low_regime_adjustment * ((1 - demand_response) * mean_demand + demand_response * last_demand)
    
    target = max(0.0, adjusted_mean * S_over_mean + target_forecast_gain * (arrival_mean - adjusted_mean))
    cap = max(0.0, adjusted_mean * cap_over_mean + cap_forecast_gain * (arrival_mean - adjusted_mean))
    
    order_amount = min(cap, max(0.0, target - inventory_gain * projected_inventory - pipeline_adjustment * total_pipeline))
    return order_amount
