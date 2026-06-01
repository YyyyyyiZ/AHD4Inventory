# sample_id: 016
# folder: deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6
# distribution: exponential_L6_c1_5
# generation: 6
# rank_in_population_file: 8
# objective: 11232.3442
# test_objective: 11214.91281
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 431.45521403586514  # OPT_PARAM: {"initial": 431.45521403586514, "min": 200, "max": 800, "type": "float"}
    safety_stock = 166.96209077603805  # OPT_PARAM: {"initial": 166.96209077603805, "min": 100, "max": 300, "type": "float"}
    demand_smoothing = 0.14593966226801802  # OPT_PARAM: {"initial": 0.14593966226801802, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.6078122160613739  # OPT_PARAM: {"initial": 0.6078122160613739, "min": 0.3, "max": 1.0, "type": "float"}
    order_smoothing = 0.1296107641229217  # OPT_PARAM: {"initial": 0.1296107641229217, "min": 0.1, "max": 0.8, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Estimate demand from recent pipeline arrivals (more stable than just first few)
    # Use weighted average with more weight on recent arrivals
    if pipeline_orders:
        weights = [0.1, 0.2, 0.3, 0.4]  # Increasing weights for more recent
        weighted_sum = 0
        total_weight = 0
        for i, qty in enumerate(pipeline_orders[-4:] if len(pipeline_orders) >= 4 else pipeline_orders):
            weight = weights[i] if i < len(weights) else 0.2
            weighted_sum += qty * weight
            total_weight += weight
        estimated_demand = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        estimated_demand = 0
    
    # Smooth demand estimate
    smoothed_demand = demand_smoothing * estimated_demand + (1 - demand_smoothing) * (base_stock / 10)
    
    # Calculate target inventory position considering pipeline
    pipeline_effect = pipeline_weight * smoothed_demand * len(pipeline_orders)
    target_position = base_stock + safety_stock + pipeline_effect
    
    # Calculate order amount with smoothing
    raw_order = max(0, target_position - inventory_position)
    # Apply order smoothing to reduce volatility
    order_amount = order_smoothing * raw_order + (1 - order_smoothing) * smoothed_demand
    
    return order_amount
