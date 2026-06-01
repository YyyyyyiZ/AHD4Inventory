# sample_id: 065
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: poisson_L6_c1_2
# generation: 10
# rank_in_population_file: 3
# objective: 839.74
# test_objective: 817.593
# is_top10_by_distribution: False
# is_final_generation: True
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 735.7792788064165  # OPT_PARAM: {"initial": 735.7792788064165, "min": 400, "max": 900, "type": "float"}
    
    # Demand anticipation parameters
    demand_anticipation_factor = 0.2058491381515156  # OPT_PARAM: {"initial": 0.2058491381515156, "min": 0.1, "max": 0.8, "type": "float"}
    recent_demand_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.9, "type": "float"}
    
    # Pipeline urgency factor
    pipeline_urgency_factor = 0.22842984269653896  # OPT_PARAM: {"initial": 0.22842984269653896, "min": 0.1, "max": 0.8, "type": "float"}
    
    # Cost-balancing parameters
    holding_cost_weight = 0.9368933615395726  # OPT_PARAM: {"initial": 0.9368933615395726, "min": 0.3, "max": 1.2, "type": "float"}
    lost_sales_cost_weight = 1.252120939146047  # OPT_PARAM: {"initial": 1.252120939146047, "min": 0.8, "max": 2.0, "type": "float"}
    
    # Order smoothing parameters
    smoothing_factor = 0.11157585598691623  # OPT_PARAM: {"initial": 0.11157585598691623, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_size = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    
    # Pipeline variability adjustment
    pipeline_variability_factor = 6.165600208464511e-06  # OPT_PARAM: {"initial": 6.165600208464511e-06, "min": 0.0, "max": 0.8, "type": "float"}
    
    # Safety stock buffer factor
    safety_buffer_factor = 0.062341482774576434  # OPT_PARAM: {"initial": 0.062341482774576434, "min": 0.0, "max": 0.5, "type": "float"}
    
    # NEW: Aggressive ordering factor for low inventory
    low_inventory_boost = 1.333272947835163  # OPT_PARAM: {"initial": 1.333272947835163, "min": 1.0, "max": 3.0, "type": "float"}
    
    # NEW: Lost sales penalty multiplier
    lost_sales_penalty = 1.5076284285199317  # OPT_PARAM: {"initial": 1.5076284285199317, "min": 1.0, "max": 3.0, "type": "float"}
    
    # Calculate pipeline urgency
    L = len(pipeline_orders)
    if L > 0:
        weighted_pipeline = 0.0
        total_weight = 0.0
        
        for i, q in enumerate(pipeline_orders):
            weight = 1.0 / (1.0 + i)
            weighted_pipeline += q * weight
            total_weight += weight
        
        effective_pipeline = weighted_pipeline / total_weight if total_weight > 0 else sum(pipeline_orders)
        
        pipeline_urgency = 0.0
        if L >= 2:
            near_pipeline = sum(pipeline_orders[:L//2])
            far_pipeline = sum(pipeline_orders[L//2:])
            total_pipeline = near_pipeline + far_pipeline
            
            if total_pipeline > 0:
                pipeline_urgency = far_pipeline / total_pipeline
    else:
        effective_pipeline = 0.0
        pipeline_urgency = 0.0
    
    # Calculate pipeline variability
    pipeline_variability = 0.0
    if L > 1:
        pipeline_mean = sum(pipeline_orders) / L
        if pipeline_mean > 0:
            pipeline_variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / L
            cv_squared = pipeline_variance / (pipeline_mean ** 2)
            pipeline_variability = cv_squared
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Dynamic safety stock
    dynamic_safety_stock = base_stock * (1.0 + pipeline_urgency * pipeline_urgency_factor)
    
    # Adjust for pipeline variability
    variability_adjustment = 1.0 + pipeline_variability * pipeline_variability_factor
    dynamic_safety_stock *= variability_adjustment
    
    # NEW: Apply low inventory boost
    inventory_ratio = inventory_position / dynamic_safety_stock
    if inventory_ratio < 0.3:
        dynamic_safety_stock *= low_inventory_boost
    
    # Cost-balanced order-up-to level with lost sales penalty
    cost_ratio = (lost_sales_cost_weight * lost_sales_penalty) / holding_cost_weight
    cost_balanced_level = dynamic_safety_stock * (1.0 + demand_anticipation_factor * (cost_ratio - 1.0))
    
    # Add safety buffer
    safety_buffer = 0.0
    if inventory_position < dynamic_safety_stock * 0.5:
        safety_buffer = safety_buffer_factor * (dynamic_safety_stock - inventory_position)
    cost_balanced_level += safety_buffer
    
    # Calculate raw order amount
    raw_order = max(0.0, cost_balanced_level - inventory_position)
    
    # Apply smoothing
    urgency_adjusted_smoothing = smoothing_factor * (1.0 - pipeline_urgency * 0.5)
    smoothed_order = raw_order * urgency_adjusted_smoothing
    
    # Apply minimum order threshold
    if smoothed_order < min_order_size:
        smoothed_order = 0.0
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
