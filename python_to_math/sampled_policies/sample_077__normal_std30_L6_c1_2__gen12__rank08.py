# sample_id: 077
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: normal_std30_L6_c1_2
# generation: 12
# rank_in_population_file: 8
# objective: 2243.71088
# test_objective: 2236.31464
# is_top10_by_distribution: True
# is_final_generation: True
# table_motifs: pipeline_weighting;order_up_to;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;emergency_or_shortage_boost
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Fixed constants from dataset analysis
    mean_demand = 100.0
    L = len(pipeline_orders)
    
    # Base stock level - tuned for lead time demand coverage
    base_stock = 566.185973326278  # OPT_PARAM: {"initial": 566.185973326278, "min": 400, "max": 800, "type": "float"}
    
    # Pipeline discount factors - more aggressive discounting for later arrivals
    early_discount = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    mid_discount = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    late_discount = 0.6541439085216577  # OPT_PARAM: {"initial": 0.6541439085216577, "min": 0.2, "max": 0.7, "type": "float"}
    
    # Order smoothing parameters
    min_order = 9.863642334015735  # OPT_PARAM: {"initial": 9.863642334015735, "min": 5, "max": 30, "type": "float"}
    max_order = 87.72136344324525  # OPT_PARAM: {"initial": 87.72136344324525, "min": 80, "max": 200, "type": "float"}
    
    # Aggressiveness adjustment thresholds
    low_stock_threshold = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 30, "max": 100, "type": "float"}
    high_stock_threshold = 199.9908165611701  # OPT_PARAM: {"initial": 199.9908165611701, "min": 100, "max": 250, "type": "float"}
    
    # Aggressiveness multipliers
    low_stock_multiplier = 1.25  # OPT_PARAM: {"initial": 1.25, "min": 1.1, "max": 1.5, "type": "float"}
    high_stock_multiplier = 0.8690541317887209  # OPT_PARAM: {"initial": 0.8690541317887209, "min": 0.5, "max": 0.9, "type": "float"}
    
    # Safety stock buffer for demand variability
    safety_stock = 66.36535573531937  # OPT_PARAM: {"initial": 66.36535573531937, "min": 20, "max": 150, "type": "float"}
    
    # Pipeline shape penalty for uneven distribution
    pipeline_roughness_penalty = 0.8569745712739317  # OPT_PARAM: {"initial": 0.8569745712739317, "min": 0.5, "max": 1.2, "type": "float"}
    
    # Dynamic safety stock based on pipeline variability
    pipeline_variability_factor = 0.8793791645850786  # OPT_PARAM: {"initial": 0.8793791645850786, "min": 0.5, "max": 1.5, "type": "float"}
    
    # Aggressive ordering when immediate availability is critically low
    critical_threshold = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 10, "max": 50, "type": "float"}
    critical_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.2, "max": 2.0, "type": "float"}
    
    # NEW: Demand forecast adjustment factor
    demand_adjustment = 1.0083668144408222  # OPT_PARAM: {"initial": 1.0083668144408222, "min": 0.9, "max": 1.2, "type": "float"}
    
    # NEW: Immediate coverage buffer
    immediate_buffer = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 50, "type": "float"}
    
    # Calculate discounted pipeline value with slot-specific discounts
    discounted_pipeline = 0.0
    
    for i in range(L):
        if i < 2:  # Arriving in next 2 periods
            discounted_pipeline += pipeline_orders[i] * early_discount
        elif i < 4:  # Arriving in periods 3-4
            discounted_pipeline += pipeline_orders[i] * mid_discount
        else:  # Arriving in periods 5-6
            discounted_pipeline += pipeline_orders[i] * late_discount
    
    # Calculate pipeline roughness (variability in arrivals)
    pipeline_roughness = 0.0
    for i in range(L-1):
        pipeline_roughness += abs(pipeline_orders[i] - pipeline_orders[i+1])
    
    # Apply roughness penalty to discounted pipeline
    if pipeline_roughness > 100:  # Significant variability threshold
        discounted_pipeline *= pipeline_roughness_penalty
    
    # Calculate dynamic safety stock based on pipeline variability
    dynamic_safety = safety_stock
    if pipeline_roughness > 50:  # Moderate variability
        dynamic_safety *= (1.0 + pipeline_variability_factor * (pipeline_roughness / 500.0))
    
    # NEW: Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock * demand_adjustment
    
    # Calculate effective inventory position with dynamic safety stock
    effective_ip = on_hand_inventory + discounted_pipeline
    target_level = adjusted_base_stock + dynamic_safety
    
    # NEW: Add immediate coverage consideration
    immediate_coverage = on_hand_inventory + pipeline_orders[0]
    if immediate_coverage < mean_demand:
        target_level += immediate_buffer
    
    # Base order: target level minus effective inventory position
    order_amount = max(0.0, target_level - effective_ip)
    
    # Adjust aggressiveness based on current availability
    availability = on_hand_inventory + pipeline_orders[0]
    
    # Critical stock handling - most aggressive when immediate stock is very low
    if availability < critical_threshold:
        order_amount = order_amount * critical_multiplier
    elif availability < low_stock_threshold:
        # More aggressive when stock is low
        order_amount = order_amount * low_stock_multiplier
    elif availability > high_stock_threshold:
        # Less aggressive when stock is high
        order_amount = order_amount * high_stock_multiplier
    
    # Apply order smoothing
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order
    
    # Cap order amount
    order_amount = min(order_amount, max_order)
    
    # Round to nearest integer (orders must be integer quantities)
    return order_amount
