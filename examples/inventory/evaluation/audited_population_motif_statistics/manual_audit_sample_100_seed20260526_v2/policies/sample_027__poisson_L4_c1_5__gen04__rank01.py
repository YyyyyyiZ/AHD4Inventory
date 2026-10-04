# sample_id: 027
# folder: deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: poisson_L4_c1_5
# generation: 4
# rank_in_population_file: 1
# objective: 1123.42
# test_objective: 1186.7
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 418.4796855242302  # OPT_PARAM: {"initial": 418.4796855242302, "min": 350, "max": 500, "type": "float"}
    
    # Safety stock multiplier
    safety_multiplier = 1.913108986256217  # OPT_PARAM: {"initial": 1.913108986256217, "min": 1.0, "max": 2.5, "type": "float"}
    
    # Demand parameters
    typical_demand = 99.80989497864154  # OPT_PARAM: {"initial": 99.80989497864154, "min": 80, "max": 120, "type": "float"}
    demand_std = 17.329580214699273  # OPT_PARAM: {"initial": 17.329580214699273, "min": 8, "max": 20, "type": "float"}
    
    # Pipeline weighting parameters
    pipeline_weight = 0.9104567322084133  # OPT_PARAM: {"initial": 0.9104567322084133, "min": 0.8, "max": 1.2, "type": "float"}
    
    # Order smoothing parameters
    max_order_change = 40  # OPT_PARAM: {"initial": 40, "min": 20, "max": 80, "type": "int"}
    typical_order = 60.2  # OPT_PARAM: {"initial": 60.2, "min": 40, "max": 90, "type": "float"}
    
    # New: Pipeline age weighting
    age_weight_power = 0.6154647503059288  # OPT_PARAM: {"initial": 0.6154647503059288, "min": 0.1, "max": 2.0, "type": "float"}
    
    # New: Demand anticipation factor
    demand_anticipation = 0.2353085324847689  # OPT_PARAM: {"initial": 0.2353085324847689, "min": 0.0, "max": 1.0, "type": "float"}
    
    # Calculate weighted pipeline with age-based discounting
    lead_time = len(pipeline_orders)
    weighted_pipeline = 0.0
    for i, order in enumerate(pipeline_orders):
        # Older orders get higher weight (closer to arrival)
        age_weight = (i + 1) ** age_weight_power
        weighted_pipeline += order * age_weight
    
    # Normalize by sum of age weights
    total_age_weight = sum((i + 1) ** age_weight_power for i in range(lead_time))
    weighted_pipeline = weighted_pipeline / total_age_weight * lead_time * pipeline_weight
    
    # Calculate safety stock with lead time consideration
    review_period = 1
    safety_stock = safety_multiplier * demand_std * ((lead_time + review_period) ** 0.5)
    
    # Adjust base stock based on demand anticipation
    adjusted_base_stock = base_stock * (1 + demand_anticipation * (typical_demand - 100) / 100)
    
    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock
    
    # Calculate current inventory position
    current_position = on_hand_inventory + weighted_pipeline
    
    # Calculate raw order amount
    raw_order = target_position - current_position
    
    # Apply order smoothing with asymmetric bounds
    if raw_order > 0:
        upper_bound = typical_order + max_order_change
        lower_bound = max(0, typical_order - max_order_change * 0.5)  # New: asymmetric smoothing
        smoothed_order = min(max(raw_order, lower_bound), upper_bound)
        order_amount = max(0, int(round(smoothed_order)))
    else:
        order_amount = 0
    
    return order_amount
