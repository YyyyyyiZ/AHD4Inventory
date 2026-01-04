# Auto-extracted policy code
# Source JSON: exponential_L6_c1_2.json
# Extracted at: 2026-01-04 09:19:33

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.0551589336057  # OPT_PARAM: {"initial": 449.0551589336057, "min": 300, "max": 600, "type": "float"}
    safety_stock = 118.25160201043154  # OPT_PARAM: {"initial": 118.25160201043154, "min": 80, "max": 180, "type": "float"}
    pipeline_weight = 0.8346281654923688  # OPT_PARAM: {"initial": 0.8346281654923688, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    lost_sales_weight = 2.3268591725381484  # OPT_PARAM: {"initial": 2.3268591725381484, "min": 1.5, "max": 2.5, "type": "float"}
    demand_buffer = 1.2480577517614566  # OPT_PARAM: {"initial": 1.2480577517614566, "min": 1.0, "max": 1.3, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}
    
    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Adjust base stock based on cost ratio and demand buffer
    adjusted_base = base_stock * lost_sales_weight * demand_buffer
    
    # Calculate target inventory level
    target = adjusted_base + safety_stock
    
    # Calculate required order
    required_order = max(0, target - inventory_position)
    
    # Apply smoothing with minimum order threshold
    if required_order > min_order_threshold:
        order_amount = int(round(required_order * smoothing_factor))
    else:
        order_amount = 0
    
    return order_amount
