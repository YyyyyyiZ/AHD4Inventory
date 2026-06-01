# sample_id: 005
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-e2_6_r1
# distribution: normal_std30_L6_c1_2
# generation: 2
# rank_in_population_file: 2
# objective: 2372.08
# test_objective: 2367.379
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level for normal operation
    base_stock = 602.7471676191776  # OPT_PARAM: {"initial": 602.7471676191776, "min": 100, "max": 1000, "type": "float"}
    
    # Safety stock buffer
    safety_stock = 57.947167619179545  # OPT_PARAM: {"initial": 57.947167619179545, "min": 0, "max": 200, "type": "float"}
    
    # Weight for pipeline orders (higher = more conservative)
    pipeline_weight = 0.6918604694768504  # OPT_PARAM: {"initial": 0.6918604694768504, "min": 0.1, "max": 1.5, "type": "float"}
    
    # Weight for on-hand inventory (higher = more aggressive)
    on_hand_weight = 0.9081860064437058  # OPT_PARAM: {"initial": 0.9081860064437058, "min": 0.5, "max": 2.0, "type": "float"}
    
    # Smoothing factor for order adjustments
    smoothing_factor = 0.14628116825983467  # OPT_PARAM: {"initial": 0.14628116825983467, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Exponential weighting for recent pipeline orders
    recent_pipeline_weight = 1.66131668224612  # OPT_PARAM: {"initial": 1.66131668224612, "min": 0.5, "max": 3.0, "type": "float"}
    
    # Minimum order threshold
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}
    
    # NEW: Pipeline variability adjustment factor
    variability_factor = 0.443389619707202  # OPT_PARAM: {"initial": 0.443389619707202, "min": 0.0, "max": 2.0, "type": "float"}
    
    # NEW: Recent demand anticipation factor
    demand_anticipation = 0.479255125254089  # OPT_PARAM: {"initial": 0.479255125254089, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Calculate weighted pipeline sum (recent orders weighted more heavily)
    weighted_pipeline_sum = 0.0
    total_weight = 0.0
    for i, order in enumerate(pipeline_orders):
        weight = recent_pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline_sum += order * weight
        total_weight += weight
    
    # Calculate effective pipeline with exponential weighting
    effective_pipeline = weighted_pipeline_sum / total_weight if total_weight > 0 else 0
    
    # NEW: Calculate pipeline variability (standard deviation)
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        pipeline_std = variance ** 0.5
    else:
        pipeline_std = 0
    
    # NEW: Adjust safety stock based on pipeline variability
    variability_adjustment = pipeline_std * variability_factor
    adjusted_safety_stock = safety_stock + variability_adjustment
    
    # NEW: Anticipate demand from recent pipeline pattern
    if effective_pipeline > 0:
        anticipated_demand = effective_pipeline * demand_anticipation
    else:
        anticipated_demand = 0
    
    # Calculate effective inventory position
    effective_on_hand = on_hand_inventory * on_hand_weight
    
    # Calculate inventory position
    inventory_position = effective_on_hand + effective_pipeline * pipeline_weight
    
    # Calculate target order using smoothed adjustment with NEW adjustments
    target_order = base_stock + adjusted_safety_stock + anticipated_demand - inventory_position
    
    # Apply smoothing to avoid drastic changes
    if target_order > 0:
        order_amount = target_order * smoothing_factor
    else:
        order_amount = 0
    
    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_threshold:
        order_amount = 0
    
    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))
    
    # Ensure non-negative
    order_amount = max(0, order_amount)
    
    return order_amount
