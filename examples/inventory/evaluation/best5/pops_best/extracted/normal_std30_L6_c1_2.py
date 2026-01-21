# Auto-extracted policy code
# Source JSON: normal_std30_L6_c1_2.json
# Extracted at: 2026-01-20 20:59:11

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 426.15027028665736  # OPT_PARAM: {"initial": 426.15027028665736, "min": 350, "max": 480, "type": "float"}
    safety_stock = 96.15027028665892  # OPT_PARAM: {"initial": 96.15027028665892, "min": 60, "max": 120, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_forecast = 120.66760596235318  # OPT_PARAM: {"initial": 120.66760596235318, "min": 95, "max": 125, "type": "float"}
    smoothing_factor = 0.08466621051419153  # OPT_PARAM: {"initial": 0.08466621051419153, "min": 0.05, "max": 0.3, "type": "float"}
    forecast_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.2, "max": 0.5, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_discount = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.8, "max": 1.0, "type": "float"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    
    # Calculate discounted pipeline inventory
    discounted_pipeline = sum(p * pipeline_discount**(i+1) for i, p in enumerate(pipeline_orders))
    
    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    effective_inventory = on_hand_inventory + weighted_pipeline
    
    # Calculate target inventory level
    target_inventory = base_stock + safety_stock
    
    # Calculate base order with discounted pipeline consideration
    base_order = max(0, target_inventory - effective_inventory + adjustment_factor * discounted_pipeline)
    
    # Add demand forecast component with adjustable weight
    forecast_order = demand_forecast * forecast_weight
    
    # Combine with smoothing
    raw_order = base_order * smoothing_factor + forecast_order * (1 - smoothing_factor)
    
    # Apply minimum order quantity
    raw_order = max(raw_order, min_order)
    
    # Ensure non-negative order
    order_amount = max(0, int(round(raw_order)))
    
    return order_amount
