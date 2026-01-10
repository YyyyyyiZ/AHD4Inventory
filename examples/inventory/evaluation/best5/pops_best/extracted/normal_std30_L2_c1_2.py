# Auto-extracted policy code
# Source JSON: normal_std30_L2_c1_2.json
# Extracted at: 2026-01-05 23:14:35

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.8921793230003  # OPT_PARAM: {"initial": 290.8921793230003, "min": 200, "max": 350, "type": "float"}
    order_cap = 92.66600210762225  # OPT_PARAM: {"initial": 92.66600210762225, "min": 80, "max": 200, "type": "float"}
    safety_stock = 70.89217932300217  # OPT_PARAM: {"initial": 70.89217932300217, "min": 40, "max": 100, "type": "float"}
    demand_adj_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.2, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Adjust base stock based on incoming pipeline (anticipate future arrivals)
    pipeline_adjustment = pipeline_weight * pipeline_orders[0] if pipeline_orders else 0
    
    # Calculate dynamic target considering safety stock and pipeline adjustment
    dynamic_target = base_stock + safety_stock - pipeline_adjustment
    
    # Calculate desired order amount with demand adjustment
    desired_order = max(0, dynamic_target - inventory_position)
    adjusted_order = desired_order * demand_adj_factor
    
    # Apply order cap and minimum order threshold
    if adjusted_order < min_order_threshold:
        order_amount = 0
    else:
        order_amount = min(max(0, adjusted_order), order_cap)
    
    return order_amount
