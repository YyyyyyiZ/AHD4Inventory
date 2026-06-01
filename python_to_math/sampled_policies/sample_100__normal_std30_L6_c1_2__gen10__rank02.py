# sample_id: 100
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-e1-e1_4_r1
# distribution: normal_std30_L6_c1_2
# generation: 10
# rank_in_population_file: 2
# objective: 2337.34
# test_objective: 2316.588
# is_top10_by_distribution: False
# is_final_generation: True
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 549.5480724239817  # OPT_PARAM: {"initial": 549.5480724239817, "min": 300, "max": 800, "type": "float"}
    
    # Pipeline volatility factor
    volatility_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Order smoothing factor
    smoothing = 0.14596725097252355  # OPT_PARAM: {"initial": 0.14596725097252355, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Critical ratio adjustment
    cr_adjust = 0.4711446868515846  # OPT_PARAM: {"initial": 0.4711446868515846, "min": -0.5, "max": 0.5, "type": "float"}
    
    # Pipeline pattern matching weight
    pattern_weight = 0.43107405757054845  # OPT_PARAM: {"initial": 0.43107405757054845, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Pattern decay factor
    pattern_decay = 0.7159501518667241  # OPT_PARAM: {"initial": 0.7159501518667241, "min": 0.5, "max": 0.95, "type": "float"}
    
    # Pattern threshold
    pattern_threshold = 0.2395822333385727  # OPT_PARAM: {"initial": 0.2395822333385727, "min": 0.05, "max": 0.5, "type": "float"}
    
    L = len(pipeline_orders)
    if L == 0:
        return int(round(base_stock - on_hand_inventory))
    
    total_pipeline = sum(pipeline_orders)
    
    # NOVEL FEATURE 1: Pipeline volatility measurement
    # Measure how much the pipeline fluctuates (standard deviation relative to mean)
    if L >= 2 and total_pipeline > 0:
        pipeline_mean = total_pipeline / L
        if pipeline_mean > 0.001:
            variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / L
            std_dev = variance ** 0.5
            volatility = std_dev / pipeline_mean
            # High volatility suggests unstable ordering - smooth more aggressively
            volatility_adjustment = 1.0 - volatility_factor * min(volatility, 2.0)
        else:
            volatility_adjustment = 1.0
    else:
        volatility_adjustment = 1.0
    
    # NOVEL FEATURE 2: Pattern-based pipeline analysis
    # Detect recurring patterns in pipeline distribution (e.g., increasing, decreasing, U-shaped)
    if L >= 3:
        # Calculate pattern scores for different archetypes
        patterns = {}
        
        # Increasing pattern (orders getting larger over time)
        inc_score = 0
        for i in range(1, L):
            if pipeline_orders[i-1] > 0.001:
                inc_score += (pipeline_orders[i] - pipeline_orders[i-1]) / pipeline_orders[i-1]
        inc_score /= max(1, L-1)
        patterns['increasing'] = max(0, inc_score)  # Only positive changes
        
        # Decreasing pattern (orders getting smaller over time)
        dec_score = 0
        for i in range(1, L):
            if pipeline_orders[i-1] > 0.001:
                dec_score += (pipeline_orders[i-1] - pipeline_orders[i]) / pipeline_orders[i-1]
        dec_score /= max(1, L-1)
        patterns['decreasing'] = max(0, dec_score)
        
        # U-shaped pattern (small in middle, large at ends)
        u_score = 0
        if L >= 3:
            mid = L // 2
            early_avg = sum(pipeline_orders[:mid]) / mid
            middle_avg = sum(pipeline_orders[mid:L-mid]) / max(1, L-2*mid)
            late_avg = sum(pipeline_orders[L-mid:]) / mid
            
            if middle_avg > 0.001:
                u_score = (early_avg + late_avg) / (2 * middle_avg) - 1.0
            u_score = max(0, u_score)
        patterns['u_shaped'] = u_score
        
        # Find strongest pattern
        strongest_pattern = max(patterns.items(), key=lambda x: x[1])
        
        # Apply pattern-based adjustment
        if strongest_pattern[1] > pattern_threshold:
            if strongest_pattern[0] == 'increasing':
                # If pipeline is increasing, we might be over-ordering - reduce slightly
                pattern_adjustment = 1.0 - pattern_weight * strongest_pattern[1] * pattern_decay
            elif strongest_pattern[0] == 'decreasing':
                # If pipeline is decreasing, we might be under-ordering - increase slightly
                pattern_adjustment = 1.0 + pattern_weight * strongest_pattern[1] * pattern_decay
            else:  # u_shaped
                # U-shaped suggests both recent and distant orders are high - maintain
                pattern_adjustment = 1.0
        else:
            pattern_adjustment = 1.0
    else:
        pattern_adjustment = 1.0
    
    # Cost-ratio adjustment (newsvendor logic)
    critical_ratio = 2.0 / (1.0 + 2.0)  # p/(h+p) = 2/3
    cost_adjusted_base = base_stock * (1.0 + cr_adjust * (critical_ratio - 0.5))
    
    # Combine adjustments
    adjusted_target = cost_adjusted_base * volatility_adjustment * pattern_adjustment
    
    # Current inventory position
    current_position = on_hand_inventory + total_pipeline
    
    # Raw order amount
    raw_order = max(0, adjusted_target - current_position)
    
    # Apply smoothing with pipeline average
    if L > 0:
        pipeline_avg = total_pipeline / L
        smoothed_order = smoothing * raw_order + (1 - smoothing) * pipeline_avg
    else:
        smoothed_order = raw_order
    
    # Ensure non-negative integer
    order_amount = int(round(max(0, smoothed_order)))
    
    return order_amount
