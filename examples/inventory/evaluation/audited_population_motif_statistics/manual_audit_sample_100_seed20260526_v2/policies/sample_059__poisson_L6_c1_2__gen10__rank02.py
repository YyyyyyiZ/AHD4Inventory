# sample_id: 059
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_e1-m2_6_r2
# distribution: poisson_L6_c1_2
# generation: 10
# rank_in_population_file: 2
# objective: 1033.1
# test_objective: 976.627
# is_top10_by_distribution: False
# is_final_generation: True
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping;order_smoothing
# extra_motifs: pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Core policy parameters
    base_target = 581.8060760782333  # OPT_PARAM: {"initial": 581.8060760782333, "min": 400, "max": 900, "type": "float"}
    demand_estimate = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    safety_factor = 0.8088798033541513  # OPT_PARAM: {"initial": 0.8088798033541513, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_decay = 0.8356706894043239  # OPT_PARAM: {"initial": 0.8356706894043239, "min": 0.5, "max": 1.0, "type": "float"}
    
    # Novel structural component: demand pattern recognition
    pipeline_gradient_threshold = 0.30615656003069885  # OPT_PARAM: {"initial": 0.30615656003069885, "min": 0.1, "max": 0.8, "type": "float"}
    gradient_response = 2.986613877539136  # OPT_PARAM: {"initial": 2.986613877539136, "min": 1.0, "max": 3.0, "type": "float"}
    
    # Calculate weighted pipeline with exponential decay
    weighted_pipeline = 0.0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_decay ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight
    
    # Novel structural logic: Detect pipeline depletion patterns
    pipeline_gradient = 0.0
    if len(pipeline_orders) >= 2:
        # Calculate slope of pipeline orders (recent vs older)
        recent_avg = sum(pipeline_orders[-2:]) / 2
        older_avg = sum(pipeline_orders[:-2]) / (len(pipeline_orders) - 2) if len(pipeline_orders) > 2 else recent_avg
        pipeline_gradient = (recent_avg - older_avg) / max(1.0, older_avg)
    
    # Adjust target based on pipeline gradient
    gradient_adjustment = 1.0
    if pipeline_gradient < -pipeline_gradient_threshold:
        # Pipeline is decreasing sharply - increase orders
        gradient_adjustment = gradient_response
    elif pipeline_gradient > pipeline_gradient_threshold:
        # Pipeline is increasing - reduce orders
        gradient_adjustment = 1.0 / gradient_response
    
    # Calculate effective inventory position
    effective_position = on_hand_inventory + weighted_pipeline
    
    # Calculate adjusted target
    adjusted_target = base_target * gradient_adjustment
    
    # Base order calculation
    base_order = max(0, adjusted_target - effective_position)
    
    # Add demand-responsive component
    demand_component = demand_estimate * safety_factor
    
    # Novel structural logic: Blend based on pipeline coverage
    pipeline_coverage_ratio = weighted_pipeline / (demand_estimate * len(pipeline_orders)) if len(pipeline_orders) > 0 else 0
    
    if pipeline_coverage_ratio < 0.8:
        # Low pipeline coverage - emphasize demand component
        blend_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.3, "max": 0.9, "type": "float"}
    elif pipeline_coverage_ratio > 1.2:
        # High pipeline coverage - emphasize base stock adjustment
        blend_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.7, "type": "float"}
    else:
        # Moderate coverage - balanced approach
        blend_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.2, "max": 0.8, "type": "float"}
    
    # Final blended order
    order_amount = blend_weight * base_order + (1 - blend_weight) * demand_component
    
    # Apply non-linear smoothing
    smoothing_factor = 0.25747925090182155  # OPT_PARAM: {"initial": 0.25747925090182155, "min": 0.05, "max": 0.5, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        order_amount = last_order + smoothing_factor * (order_amount - last_order)
    
    # Ensure non-negative and integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))
    
    return order_amount
