import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 280.0  # OPT_PARAM: {"initial": 280.0, "min": 280.0, "max": 360.0, "type": "float"}
    demand_response = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    inventory_adjustment = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.4, "type": "float"}
    
    # Detect demand regime shift (high/low demand periods)
    high_demand = last_demand >= 100.0 * np.log(2)
    regime_factor = 1.5 if high_demand else 1.0
    
    dynamic_target = base_target * regime_factor + demand_response * last_demand
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, inventory_adjustment * (dynamic_target - inventory_position))
    return order_amount
