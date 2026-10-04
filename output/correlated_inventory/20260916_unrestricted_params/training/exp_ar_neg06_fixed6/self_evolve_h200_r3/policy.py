import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_target = 463.10603258410646  # OPT_PARAM: {"initial": 463.10603258410646, "min": 400.0, "max": 600.0, "type": "float"}
    demand_response = 4.849346725762212  # OPT_PARAM: {"initial": 4.849346725762212, "min": 2.0, "max": 5.0, "type": "float"}
    smoothing = 0.11844717809705342  # OPT_PARAM: {"initial": 0.11844717809705342, "min": 0.05, "max": 0.3, "type": "float"}
    z_response = 0.9506608155618251  # OPT_PARAM: {"initial": 0.9506608155618251, "min": 0.0, "max": 1.0, "type": "float"}
    demand_floor = 76.89466952926657  # OPT_PARAM: {"initial": 76.89466952926657, "min": 20.0, "max": 80.0, "type": "float"}
    inventory_response = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Infer previous latent Z from last_demand
    z_prev = np.log(1 - np.exp(-last_demand/100.0)) * -1
    z_prev = np.minimum(3.5, np.maximum(-3.5, z_prev))
    
    # Improved demand estimation with more aggressive response
    estimated_next_demand = max(demand_floor, -100.0 * np.log(1 - 0.5 * (1 + np.tanh(-0.6 * z_prev))))
    
    # Enhanced dynamic target considering both demand and inventory position
    dynamic_target = (base_target + 
                     demand_response * estimated_next_demand + 
                     z_response * z_prev * 20.0 +
                     inventory_response * (base_target - on_hand_inventory))
    
    current_position = on_hand_inventory + sum(pipeline_orders)
    order_amount = max(0.0, smoothing * (dynamic_target - current_position))
    
    return order_amount
