# sample_id: 013
# folder: deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_e1-e1-e1_4_r1
# distribution: exponential_L6_c1_2
# generation: 9
# rank_in_population_file: 2
# objective: 6027.72
# test_objective: 6152.459
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 303.5203530187662  # OPT_PARAM: {"initial": 303.5203530187662, "min": 100, "max": 800, "type": "float"}
    
    # Critical ratio for newsvendor-like adjustment
    critical_ratio = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    
    # Pipeline pattern recognition sensitivity
    pattern_sensitivity = 0.20257569496074482  # OPT_PARAM: {"initial": 0.20257569496074482, "min": 0.0, "max": 2.0, "type": "float"}
    
    # Order smoothing factor
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Minimum order quantity
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}
    
    # Maximum order quantity
    max_order = 800.0  # OPT_PARAM: {"initial": 800.0, "min": 200, "max": 1500, "type": "float"}
    
    # NEW STRUCTURAL ELEMENT: Pattern-based demand forecasting
    # Instead of just averaging pipeline, we detect specific patterns:
    # 1. Increasing trend
    # 2. Decreasing trend  
    # 3. Spike pattern
    # 4. Stable pattern
    
    L = len(pipeline_orders)
    
    if L >= 3:
        # Split pipeline into thirds for pattern analysis
        third = L // 3
        if third == 0:
            third = 1
            
        # Calculate averages for each third
        first_avg = sum(pipeline_orders[:third]) / third
        second_avg = sum(pipeline_orders[third:2*third]) / third if 2*third <= L else sum(pipeline_orders[third:]) / (L - third)
        third_avg = sum(pipeline_orders[2*third:]) / (L - 2*third) if 2*third < L else 0
        
        # Detect pattern
        if third_avg > 0:
            trend_ratio = (third_avg - first_avg) / third_avg
        else:
            trend_ratio = 0
            
        # Calculate volatility
        pipeline_mean = sum(pipeline_orders) / L
        if pipeline_mean > 0 and L > 1:
            variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / L
            volatility = variance ** 0.5 / pipeline_mean
        else:
            volatility = 0.0
            
        # Pattern classification and adjustment
        if abs(trend_ratio) > 0.3:
            # Strong trend detected
            if trend_ratio > 0:
                # Increasing trend - anticipate higher demand
                pattern_adjustment = pattern_sensitivity * trend_ratio * base_stock
            else:
                # Decreasing trend - anticipate lower demand
                pattern_adjustment = pattern_sensitivity * trend_ratio * base_stock * 0.5
        elif volatility > 0.5:
            # High volatility - spike pattern
            pattern_adjustment = pattern_sensitivity * volatility * base_stock * 0.3
        else:
            # Stable pattern
            pattern_adjustment = 0
    else:
        pattern_adjustment = 0
        volatility = 0.0
    
    # NEW STRUCTURAL ELEMENT: Newsvendor-inspired adjustment
    # Use critical ratio (p/(p+h)) to adjust safety stock
    # Higher critical ratio → more aggressive ordering
    newsvendor_factor = critical_ratio * 2 - 1  # Maps [0.5, 0.9] to [0, 0.8]
    
    # Calculate safety stock with volatility adjustment
    safety_stock = base_stock * 0.2 * (1 + newsvendor_factor + volatility)
    
    # Calculate total adjustment
    adjusted_base_stock = base_stock + pattern_adjustment + safety_stock
    
    # Calculate current inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Basic order calculation
    raw_order = max(0, adjusted_base_stock - net_inventory)
    
    # Apply smoothing using weighted average of pipeline as reference
    if L > 0:
        # Weight recent pipeline orders more heavily
        weighted_ref = 0
        total_weight = 0
        for i, q in enumerate(pipeline_orders):
            weight = (L - i) / L  # Linear weights
            weighted_ref += q * weight
            total_weight += weight
        
        reference_order = weighted_ref / total_weight if total_weight > 0 else raw_order
        
        # Smooth towards reference
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * reference_order
    else:
        smoothed_order = raw_order
    
    # Apply constraints
    order_amount = int(round(max(min_order, min(max_order, smoothed_order))))
    
    return order_amount
