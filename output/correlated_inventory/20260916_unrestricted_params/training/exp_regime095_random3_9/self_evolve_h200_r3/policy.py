import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    low_base_target = 112.82157981768405  # OPT_PARAM: {"initial": 112.82157981768405, "min": 80.0, "max": 150.0, "type": "float"}
    high_base_target = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 200.0, "max": 400.0, "type": "float"}
    lead_time_sensitivity = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 5.0, "max": 15.0, "type": "float"}
    demand_response = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.6, "type": "float"}
    
    # Detect demand regime
    is_high_demand = last_demand >= 100.0 * np.log(2)
    
    # Select base target based on regime
    base_target = high_base_target if is_high_demand else low_base_target
    
    # Adjust target based on lead time and recent demand
    adjusted_target = base_target + (lead_time_sensitivity * (quoted_lead_time - 6)) + (demand_response * last_demand)
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders[:quoted_lead_time])
    
    # Place order to reach adjusted target
    order_amount = max(0.0, adjusted_target - net_inventory)
    return order_amount
