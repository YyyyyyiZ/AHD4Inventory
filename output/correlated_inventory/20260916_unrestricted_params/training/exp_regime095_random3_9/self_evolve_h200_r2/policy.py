import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_level = 211.12623267442575  # OPT_PARAM: {"initial": 211.12623267442575, "min": 150.0, "max": 220.0, "type": "float"}
    demand_multiplier = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.1, "max": 1.5, "type": "float"}
    lead_time_adjustment = 0.35  # OPT_PARAM: {"initial": 0.35, "min": 0.35, "max": 0.45, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.4, "type": "float"}
    regime_multiplier = 2.2  # OPT_PARAM: {"initial": 2.2, "min": 1.5, "max": 2.2, "type": "float"}
    regime_threshold = 100.0 * np.log(2)  # 69.3147
    
    pipeline_total = np.sum(pipeline_orders)
    is_high_demand = last_demand >= regime_threshold
    
    regime_adjusted_base = base_level * (regime_multiplier if is_high_demand else 1.0)
    
    demand_estimate = last_demand * (1.3 if is_high_demand else 1.0)
    lead_time_factor = lead_time_adjustment ** (quoted_lead_time - 3)
    
    target = (regime_adjusted_base + 
             demand_multiplier * demand_estimate * lead_time_factor)
    
    smoothed_target = smoothing_factor * target + (1 - smoothing_factor) * (on_hand_inventory + pipeline_total)
    
    order_amount = max(0.0, smoothed_target - on_hand_inventory - pipeline_total)
    return order_amount
