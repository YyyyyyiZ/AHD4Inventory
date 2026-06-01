# sample_id: 032
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_e1-e2_6_r1
# distribution: exponential_L6_c1_2
# generation: 5
# rank_in_population_file: 5
# objective: 6068.0
# test_objective: 6159.841
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 389.9862343918401  # OPT_PARAM: {"initial": 389.9862343918401, "min": 200.0, "max": 600.0, "type": "float"}
    
    # Demand anticipation factor (lookahead adjustment)
    lookahead_factor = 0.8545657923765599  # OPT_PARAM: {"initial": 0.8545657923765599, "min": 0.3, "max": 1.5, "type": "float"}
    
    # Pipeline shape penalty (penalizes uneven distribution)
    shape_penalty = 0.40742876509371084  # OPT_PARAM: {"initial": 0.40742876509371084, "min": 0.0, "max": 0.5, "type": "float"}
    
    # Order smoothing factor
    smoothing = 0.13403118760093807  # OPT_PARAM: {"initial": 0.13403118760093807, "min": 0.0, "max": 0.8, "type": "float"}
    
    # Minimum order threshold
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0.0, "max": 30.0, "type": "float"}
    
    # Critical ratio adjustment (newsvendor-like)
    critical_ratio = 0.645682997278703  # OPT_PARAM: {"initial": 0.645682997278703, "min": 0.5, "max": 0.9, "type": "float"}
    
    # Pipeline variability safety factor
    safety_multiplier = 0.29881913103080476  # OPT_PARAM: {"initial": 0.29881913103080476, "min": 0.1, "max": 2.0, "type": "float"}
    
    # Pipeline trend factor for demand prediction
    trend_factor = 0.9932500500007628  # OPT_PARAM: {"initial": 0.9932500500007628, "min": 0.3, "max": 1.5, "type": "float"}
    
    # Calculate total pipeline inventory
    total_pipeline = sum(pipeline_orders)
    
    # Calculate pipeline shape penalty
    L = len(pipeline_orders)
    if L >= 2:
        # Split into first half and second half
        split = L // 2
        first_half = sum(pipeline_orders[:split])
        second_half = sum(pipeline_orders[split:])
        
        # Calculate imbalance (0 = balanced, >0 = imbalanced)
        if first_half + second_half > 0:
            imbalance = abs(first_half - second_half) / (first_half + second_half)
        else:
            imbalance = 0.0
        
        # Apply penalty proportional to imbalance
        shape_adjustment = shape_penalty * imbalance * base_stock
    else:
        shape_adjustment = 0.0
    
    # Calculate lookahead adjustment with exponential decay
    weighted_pipeline = 0.0
    for i, q in enumerate(pipeline_orders):
        weight = lookahead_factor ** (L - i - 1)
        weighted_pipeline += q * weight
    
    # NEW: Calculate pipeline trend for demand prediction
    trend_adjustment = 0.0
    if L >= 2:
        # Compare recent vs older pipeline orders to estimate demand trend
        recent_periods = min(3, L)
        recent_sum = sum(pipeline_orders[:recent_periods])
        older_sum = sum(pipeline_orders[recent_periods:]) if L > recent_periods else 0
        
        if older_sum > 0 and recent_periods > 0:
            recent_avg = recent_sum / recent_periods
            older_avg = older_sum / (L - recent_periods) if L > recent_periods else recent_avg
            demand_trend = recent_avg - older_avg
            trend_adjustment = trend_factor * demand_trend * 2.0  # Scale adjustment
    
    # Calculate effective inventory position with lookahead
    effective_inventory = on_hand_inventory + weighted_pipeline
    
    # Calculate critical ratio adjustment
    ratio_adjustment = (critical_ratio - 0.667) * 100.0
    
    # Calculate pipeline variability safety stock
    if len(pipeline_orders) > 1:
        mean_pipeline = total_pipeline / len(pipeline_orders)
        variance = sum((q - mean_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        pipeline_std = variance ** 0.5
        safety_stock = safety_multiplier * pipeline_std
    else:
        safety_stock = 0.0
    
    # Calculate target inventory position with all adjustments
    target_inventory = base_stock + ratio_adjustment - shape_adjustment + safety_stock + trend_adjustment
    
    # Calculate basic order amount
    basic_order = max(0, target_inventory - effective_inventory)
    
    # Apply smoothing with previous order (if available)
    if L > 0:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing * basic_order + (1 - smoothing) * previous_order
    else:
        smoothed_order = basic_order
    
    # Apply minimum order threshold
    if smoothed_order < min_order:
        order_amount = 0
    else:
        order_amount = int(round(smoothed_order))
    
    return order_amount
