# sample_id: 037
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-m2_6_r2
# distribution: normal_std30_L6_c1_2
# generation: 7
# rank_in_population_file: 4
# objective: 2404.84
# test_objective: 2406.131
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;order_clipping
# extra_motifs: safety_stock_buffer;threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Core inventory parameters
    base_stock = 598.921328373424  # OPT_PARAM: {"initial": 598.921328373424, "min": 300, "max": 900, "type": "float"}
    safety_stock = 150.59173522735384  # OPT_PARAM: {"initial": 150.59173522735384, "min": 50, "max": 300, "type": "float"}
    
    # NEW STRUCTURAL FEATURE: Pipeline volatility assessment
    volatility_sensitivity = 0.2574739274873779  # OPT_PARAM: {"initial": 0.2574739274873779, "min": 0.1, "max": 1.0, "type": "float"}
    smoothing_factor = 0.08936848187184449  # OPT_PARAM: {"initial": 0.08936848187184449, "min": 0.05, "max": 0.5, "type": "float"}
    
    # NEW STRUCTURAL FEATURE: Asymmetric response parameters
    shortage_response = 1.6258079301377846  # OPT_PARAM: {"initial": 1.6258079301377846, "min": 1.0, "max": 2.0, "type": "float"}
    excess_response = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
    
    # NEW STRUCTURAL FEATURE: Pipeline pattern recognition
    pattern_weight = 0.421263036256311  # OPT_PARAM: {"initial": 0.421263036256311, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0.0, "max": 30.0, "type": "float"}
    
    # Calculate pipeline volatility - NEW DECISION LOGIC
    # Measures variability in pipeline orders (standard deviation relative to mean)
    L = len(pipeline_orders)
    if L > 1:
        pipeline_mean = sum(pipeline_orders) / L
        if pipeline_mean > 0:
            variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / L
            volatility = (variance ** 0.5) / pipeline_mean
        else:
            volatility = 0.0
    else:
        volatility = 0.0
    
    # NEW STRUCTURAL FEATURE: Detect pipeline patterns
    # Identify increasing/decreasing trends in pipeline
    if L >= 3:
        # Calculate trend using linear regression slope
        x_mean = (L - 1) / 2
        y_mean = sum(pipeline_orders) / L
        
        numerator = sum((i - x_mean) * (q - y_mean) for i, q in enumerate(pipeline_orders))
        denominator = sum((i - x_mean) ** 2 for i in range(L))
        
        if denominator > 0:
            trend_slope = numerator / denominator
            # Normalize trend to [-1, 1] range
            max_possible_slope = max(abs(q) for q in pipeline_orders) if pipeline_orders else 1
            normalized_trend = trend_slope / (max_possible_slope + 1e-6)
            normalized_trend = max(-1.0, min(1.0, normalized_trend))
        else:
            normalized_trend = 0.0
    else:
        normalized_trend = 0.0
    
    # Adjust safety stock based on pipeline volatility
    # Higher volatility → higher safety stock
    volatility_adjusted_safety = safety_stock * (1.0 + volatility_sensitivity * volatility)
    
    # Calculate effective inventory position with pattern adjustment
    # Trend-aware weighting: discount future orders if pipeline is decreasing
    if L > 0:
        if normalized_trend < 0:  # Decreasing pipeline
            # Give more weight to near-term orders
            weights = [1.0 - i * abs(normalized_trend) / L for i in range(L)]
            weights = [max(0.1, w) for w in weights]  # Ensure positive weights
        elif normalized_trend > 0:  # Increasing pipeline
            # Give more weight to future orders
            weights = [0.5 + i * normalized_trend / L for i in range(L)]
        else:  # No clear trend
            weights = [1.0] * L
        
        # Normalize weights
        weight_sum = sum(weights)
        effective_pipeline = sum(w * q for w, q in zip(weights, pipeline_orders)) / weight_sum if weight_sum > 0 else 0
    else:
        effective_pipeline = 0.0
    
    # Apply pattern-based adjustment to pipeline estimate
    pattern_adjusted_pipeline = effective_pipeline * (1.0 + pattern_weight * normalized_trend)
    
    effective_inventory = on_hand_inventory + pattern_adjusted_pipeline
    
    # Calculate target inventory
    target_inventory = base_stock + volatility_adjusted_safety
    
    # Calculate order gap with asymmetric response
    order_gap = target_inventory - effective_inventory
    
    # NEW STRUCTURAL FEATURE: Asymmetric smoothing
    # Respond more aggressively to shortages, less aggressively to excess
    if order_gap > 0:  # Shortage situation
        response_factor = shortage_response
    else:  # Excess inventory situation (order_gap <= 0)
        response_factor = excess_response
        order_gap = 0  # No ordering when we have excess
    
    # Apply smoothing with asymmetric response
    smoothed_order = smoothing_factor * response_factor * order_gap
    
    # Apply minimum order threshold
    if smoothed_order < min_order_threshold:
        order_amount = 0
    else:
        order_amount = max(0, int(round(smoothed_order)))
    
    return order_amount
