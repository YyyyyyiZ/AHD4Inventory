# sample_id: 004
# folder: deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: poisson_L6_c1_5
# generation: 8
# rank_in_population_file: 2
# objective: 1238.22
# test_objective: 1272.82
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 583.5806013968356  # OPT_PARAM: {"initial": 583.5806013968356, "min": 400, "max": 800, "type": "float"}
    
    # Safety stock adjustment
    safety_stock = 122.3200350131986  # OPT_PARAM: {"initial": 122.3200350131986, "min": 20, "max": 150, "type": "float"}
    
    # Demand anticipation factor
    anticipation_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 1.5, "type": "float"}
    
    # Order smoothing
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    
    # Order bounds
    min_order = 96.64831031968099  # OPT_PARAM: {"initial": 96.64831031968099, "min": 20, "max": 100, "type": "float"}
    max_order = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 100, "max": 300, "type": "float"}
    
    # Pipeline urgency adjustment
    urgency_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    urgency_threshold = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 10, "max": 150, "type": "float"}
    
    # Lead time demand coverage
    coverage_periods = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.0, "type": "float"}
    
    # NEW: Cost-ratio adjustment factor
    cost_ratio_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    
    # NEW: Predictive ordering based on pipeline pattern recognition
    pattern_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}
    
    # NEW: Dynamic risk adjustment based on inventory position
    risk_sensitivity = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate near-term demand using weighted average of recent pipeline arrivals
    weighted_demand_estimate = 0
    total_weight = 0
    L = len(pipeline_orders)
    
    for i, q in enumerate(pipeline_orders):
        # Weight decreases for older pipeline orders
        weight = (L - i) / L
        weighted_demand_estimate += q * weight
        total_weight += weight
    
    if total_weight > 0:
        avg_weighted_demand = weighted_demand_estimate / total_weight
    else:
        avg_weighted_demand = 100.0  # Default estimate
    
    # NEW: Pattern recognition - detect if pipeline shows increasing/decreasing trend
    if L >= 3:
        recent_trend = 0
        for i in range(L-1):
            if pipeline_orders[i+1] > pipeline_orders[i]:
                recent_trend += 1
            elif pipeline_orders[i+1] < pipeline_orders[i]:
                recent_trend -= 1
        
        # Adjust demand estimate based on trend
        trend_factor = 1.0 + (recent_trend / L) * pattern_weight
        pattern_adjusted_demand = avg_weighted_demand * trend_factor
    else:
        pattern_adjusted_demand = avg_weighted_demand
    
    # Adjust base stock based on demand anticipation
    adjusted_base_stock = base_stock + anticipation_factor * (pattern_adjusted_demand - 100.0)
    
    # Apply pipeline urgency adjustment
    near_pipeline = sum(pipeline_orders[:min(2, L)])
    if near_pipeline < urgency_threshold:
        urgency_adjustment = 1.0 + (urgency_threshold - near_pipeline) / urgency_threshold * (urgency_factor - 1.0)
        adjusted_base_stock *= urgency_adjustment
    
    # Ensure lead time demand coverage
    lead_time_demand = pattern_adjusted_demand * L
    coverage_adjustment = lead_time_demand * coverage_periods
    final_base_stock = max(adjusted_base_stock, coverage_adjustment)
    
    # NEW: Dynamic risk adjustment based on current inventory position
    # Higher inventory reduces risk sensitivity, lower inventory increases it
    risk_adjustment = 1.0 + (risk_sensitivity * (1.0 - min(1.0, inventory_position / final_base_stock)))
    final_base_stock *= risk_adjustment
    
    # Adjust for cost ratio (p/h = 5/1 = 5)
    # Higher p/h ratio favors higher inventory to avoid stockouts
    cost_adjusted_base_stock = final_base_stock * cost_ratio_factor
    
    # Add safety stock
    target_inventory_position = cost_adjusted_base_stock + safety_stock
    
    # Calculate raw order
    raw_order = max(0, target_inventory_position - inventory_position)
    
    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * min_order
    
    # Apply bounds
    bounded_order = max(min_order, min(max_order, smoothed_order))
    
    # Round to nearest integer
    order_amount = int(round(bounded_order))
    
    return order_amount
