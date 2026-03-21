def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 696.0329463372658  # OPT_PARAM: {"initial": 696.0329463372658, "min": 650, "max": 750, "type": "float"}
    safety_stock = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 80, "max": 120, "type": "float"}
    demand_estimate = 95.40144044457337  # OPT_PARAM: {"initial": 95.40144044457337, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}
    adjustment_factor = 0.9580993026961738  # OPT_PARAM: {"initial": 0.9580993026961738, "min": 0.7, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time
    
    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Use base_stock as primary target
    order_up_to = base_stock
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply adjustment factor
    order_amount = order_amount * adjustment_factor
    
    # Apply smoothing for large orders
    if order_amount > demand_estimate:
        order_amount = demand_estimate + smoothing_factor * (order_amount - demand_estimate)
    
    return order_amount
