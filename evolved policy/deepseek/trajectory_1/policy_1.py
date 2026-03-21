def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 675.9310156085927  # OPT_PARAM: {"initial": 675.9310156085927, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply smoothing to reduce order volatility
    if order_amount > demand_estimate * 2:
        order_amount = demand_estimate * 2 + smoothing_factor * (order_amount - demand_estimate * 2)
    
    return order_amount
