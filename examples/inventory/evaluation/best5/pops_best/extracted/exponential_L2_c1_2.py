# Auto-extracted policy code
# Source JSON: exponential_L2_c1_2.json
# Extracted at: 2026-01-05 23:14:35

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 242.59159526283833  # OPT_PARAM: {"initial": 242.59159526283833, "min": 150, "max": 500, "type": "float"}
    pipeline_coverage = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}
    safety_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.5, "type": "float"}
    min_order = 38.03550749468216  # OPT_PARAM: {"initial": 38.03550749468216, "min": 5, "max": 50, "type": "float"}
    max_order = 67.12742187820223  # OPT_PARAM: {"initial": 67.12742187820223, "min": 60, "max": 300, "type": "float"}
    
    # Calculate effective pipeline: sum of upcoming orders weighted by lead time
    effective_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # higher weight for nearer arrivals
        effective_pipeline += q * weight
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Base order: base_stock minus inventory position
    base_order = base_stock - inventory_position
    
    # Adjust for pipeline coverage: ensure we have enough to cover pipeline-weighted demand
    pipeline_adjustment = max(0, pipeline_coverage * effective_pipeline - sum(pipeline_orders))
    
    # Safety adjustment based on current inventory level
    safety_adjustment = safety_factor * max(0, base_stock * 0.3 - on_hand_inventory)
    
    # Combine adjustments
    desired_order = base_order + pipeline_adjustment + safety_adjustment
    
    # Apply bounds and ensure non-negative
    order_amount = max(min_order, min(desired_order, max_order))
    
    return order_amount
