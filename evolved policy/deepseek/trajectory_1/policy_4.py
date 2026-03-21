def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 724.7303350610113  # OPT_PARAM: {"initial": 724.7303350610113, "min": 600, "max": 750, "type": "float"}
    safety_stock = 86.5494362894458  # OPT_PARAM: {"initial": 86.5494362894458, "min": 50, "max": 100, "type": "float"}
    demand_estimate = 95.26751014552028  # OPT_PARAM: {"initial": 95.26751014552028, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time
    
    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Use base_stock as primary target, adjusted by safety stock
    order_up_to = 0.8 * base_stock + 0.2 * target_inventory
    
    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply adjustment factor
    order_amount = order_amount * adjustment_factor
    
    # Apply smoothing for large orders
    if order_amount > demand_estimate:
        order_amount = demand_estimate + smoothing_factor * (order_amount - demand_estimate)
    
    return order_amount
