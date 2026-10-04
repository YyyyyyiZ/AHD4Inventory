import numpy as np

def compute_order_amount(on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time):
    base_stock = 312.21467830087937  # OPT_PARAM: {"initial": 312.21467830087937, "min": 300.0, "max": 500.0, "type": "float"}
    demand_response = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    lead_time_weight = 14.388947217947239  # OPT_PARAM: {"initial": 14.388947217947239, "min": 5.0, "max": 15.0, "type": "float"}
    adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.3, "type": "float"}
    
    # More sensitive demand regime detection
    is_high_demand = last_demand >= 100.0 * np.log(2)
    
    # Dynamic base stock adjustment
    adjusted_base = base_stock * (2.5 if is_high_demand else 1.0)
    
    # Target inventory calculation with stronger lead time response
    target = adjusted_base + demand_response * last_demand + lead_time_weight * (quoted_lead_time - 6)
    
    # Current pipeline inventory
    current_pipeline = on_hand_inventory + sum(pipeline_orders)
    
    # Order amount calculation
    order_amount = max(0.0, (target - current_pipeline) * adjustment_factor)
    return order_amount
