# Auto-extracted policy code
# Source JSON: poisson_L2_c1_2.json
# Extracted at: 2026-01-05 23:14:35

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 1159.6930711817074  # OPT_PARAM: {"initial": 1159.6930711817074, "min": 800, "max": 1300, "type": "float"}
    safety_stock = 79.99993441394227  # OPT_PARAM: {"initial": 79.99993441394227, "min": 20, "max": 150, "type": "float"}
    order_cap = 100.58691877701865  # OPT_PARAM: {"initial": 100.58691877701865, "min": 50, "max": 200, "type": "float"}
    adjustment_factor = 2.5  # OPT_PARAM: {"initial": 2.5, "min": 1.0, "max": 2.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate target order amount with smoothing
    target_order = (base_stock - inventory_position) * smoothing_factor
    
    # Apply safety stock adjustment with less aggressive threshold
    if inventory_position < safety_stock:
        safety_adjustment = (safety_stock - inventory_position) * adjustment_factor
        target_order = max(target_order, safety_adjustment)
    
    # Apply order cap and ensure non-negative
    order_amount = max(0, min(target_order, order_cap))
    
    # Round to nearest integer
    return order_amount
