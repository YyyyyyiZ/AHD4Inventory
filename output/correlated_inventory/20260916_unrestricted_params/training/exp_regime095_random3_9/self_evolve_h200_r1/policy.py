import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target_low = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 150.0, "max": 220.0, "type": "float"}
    base_target_high = 257.7897900682332  # OPT_PARAM: {"initial": 257.7897900682332, "min": 250.0, "max": 320.0, "type": "float"}
    response_factor_low = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    response_factor_high = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    
    prev_regime = 1 if last_demand >= 100.0 * np.log(2) else 0
    
    base_target = base_target_high if prev_regime else base_target_low
    response_factor = response_factor_high if prev_regime else response_factor_low
    
    smoothed_demand = demand_smoothing * last_demand + (1 - demand_smoothing) * base_target
    adjusted_target = base_target + response_factor * (smoothed_demand - base_target)
    
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + weighted_pipeline
    
    order_amount = max(0.0, adjusted_target - inventory_position)
    
    return order_amount
