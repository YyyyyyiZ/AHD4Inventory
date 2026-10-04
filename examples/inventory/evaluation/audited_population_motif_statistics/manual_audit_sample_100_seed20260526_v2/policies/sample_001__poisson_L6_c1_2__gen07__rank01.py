# sample_id: 001
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: poisson_L6_c1_2
# generation: 7
# rank_in_population_file: 1
# objective: 816.14
# test_objective: 793.642
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;order_up_to;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Core parameters
    base_stock = 852.0694799766587  # OPT_PARAM: {"initial": 852.0694799766587, "min": 400, "max": 900, "type": "float"}
    
    # Demand anticipation parameters
    demand_anticipation_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    recent_demand_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.9, "type": "float"}
    
    # Pipeline urgency factor
    pipeline_urgency_factor = 0.5795120417177109  # OPT_PARAM: {"initial": 0.5795120417177109, "min": 0.1, "max": 0.8, "type": "float"}
    
    # Cost-balancing parameters
    holding_cost_weight = 0.8138365213306138  # OPT_PARAM: {"initial": 0.8138365213306138, "min": 0.3, "max": 1.2, "type": "float"}
    lost_sales_cost_weight = 1.4091129587809088  # OPT_PARAM: {"initial": 1.4091129587809088, "min": 0.8, "max": 2.0, "type": "float"}
    
    # Order smoothing parameters
    smoothing_factor = 0.13063463854289023  # OPT_PARAM: {"initial": 0.13063463854289023, "min": 0.1, "max": 0.5, "type": "float"}
    min_order_size = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    
    # NEW: Safety stock parameters
    safety_stock = 220.0  # OPT_PARAM: {"initial": 220.0, "min": 150, "max": 300, "type": "float"}
    safety_adjustment_factor = 0.3038678010386268  # OPT_PARAM: {"initial": 0.3038678010386268, "min": 0.1, "max": 0.6, "type": "float"}
    lost_sales_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.2, "max": 2.0, "type": "float"}
    
    # Calculate pipeline urgency
    L = len(pipeline_orders)
    if L > 0:
        # Calculate weighted pipeline with exponential decay for urgency
        weighted_pipeline = 0.0
        total_weight = 0.0
        
        for i, q in enumerate(pipeline_orders):
            # Exponential decay: more urgent for orders arriving soon
            weight = 1.0 / (1.0 + i)  # Simple reciprocal weighting
            weighted_pipeline += q * weight
            total_weight += weight
        
        effective_pipeline = weighted_pipeline / total_weight if total_weight > 0 else sum(pipeline_orders)
        
        # Calculate pipeline urgency based on distribution
        pipeline_urgency = 0.0
        if L >= 2:
            # Measure how concentrated pipeline is in near future
            near_pipeline = sum(pipeline_orders[:L//2])
            far_pipeline = sum(pipeline_orders[L//2:])
            total_pipeline = near_pipeline + far_pipeline
            
            if total_pipeline > 0:
                # Higher urgency if more pipeline is in distant future
                pipeline_urgency = far_pipeline / total_pipeline
    else:
        effective_pipeline = 0.0
        pipeline_urgency = 0.0
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline
    
    # Dynamic safety stock based on pipeline urgency
    dynamic_safety_stock = base_stock * (1.0 + pipeline_urgency * pipeline_urgency_factor)
    
    # NEW: Safety stock deficit adjustment
    safety_adjusted_level = dynamic_safety_stock
    if inventory_position < safety_stock:
        deficit_ratio = max(0, (safety_stock - inventory_position) / max(1, safety_stock))
        adjustment = safety_adjustment_factor * (1.0 + deficit_ratio * lost_sales_multiplier)
        safety_adjusted_level += adjustment
    
    # Cost-balanced order-up-to level
    cost_ratio = lost_sales_cost_weight / holding_cost_weight
    cost_balanced_level = safety_adjusted_level * (1.0 + demand_anticipation_factor * (cost_ratio - 1.0))
    
    # Calculate raw order amount
    raw_order = max(0.0, cost_balanced_level - inventory_position)
    
    # Apply pipeline-urgency-adjusted smoothing
    urgency_adjusted_smoothing = smoothing_factor * (1.0 - pipeline_urgency * 0.5)
    smoothed_order = raw_order * urgency_adjusted_smoothing
    
    # Apply minimum order threshold
    if smoothed_order < min_order_size:
        smoothed_order = 0.0
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
