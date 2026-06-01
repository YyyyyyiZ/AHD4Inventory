# sample_id: 062
# folder: deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_2_r1
# distribution: normal_std50_L6_c1_2
# generation: 12
# rank_in_population_file: 1
# objective: 3793.52
# test_objective: 3791.56
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: pipeline_weighting;nonlinear_pipeline_composition;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding;emergency_or_shortage_boost;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 642.5315011025823  # OPT_PARAM: {"initial": 642.5315011025823, "min": 400, "max": 900, "type": "float"}
    safety_stock_multiplier = 1.3757177793014963  # OPT_PARAM: {"initial": 1.3757177793014963, "min": 1.0, "max": 3.0, "type": "float"}
    demand_smoothing = 0.35  # OPT_PARAM: {"initial": 0.35, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_decay = 0.7183866101559002  # OPT_PARAM: {"initial": 0.7183866101559002, "min": 0.4, "max": 0.9, "type": "float"}
    order_aggressiveness = 0.7099305808723362  # OPT_PARAM: {"initial": 0.7099305808723362, "min": 0.5, "max": 1.0, "type": "float"}
    
    min_order_qty = 20  # OPT_PARAM: {"initial": 20, "min": 10, "max": 30, "type": "int"}
    max_order_qty = 220  # OPT_PARAM: {"initial": 220, "min": 150, "max": 300, "type": "int"}
    
    pipeline_lookback = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 6, "type": "int"}
    demand_estimation_window = 5  # OPT_PARAM: {"initial": 5, "min": 3, "max": 8, "type": "int"}
    
    # Calculate weighted pipeline inventory with exponential decay
    weighted_pipeline = 0.0
    current_weight = 1.0
    for i in range(min(pipeline_lookback, len(pipeline_orders))):
        weighted_pipeline += pipeline_orders[i] * current_weight
        current_weight *= pipeline_decay
    
    # Estimate demand using recent pipeline orders (proxy for recent sales)
    if len(pipeline_orders) >= demand_estimation_window:
        recent_orders = pipeline_orders[:demand_estimation_window]
        estimated_demand = sum(recent_orders) / len(recent_orders)
    else:
        estimated_demand = 100.0  # fallback estimate
    
    # Calculate safety stock based on estimated demand
    safety_stock = safety_stock_multiplier * estimated_demand
    
    # Target inventory level considering base stock and safety stock
    target_inv_level = base_stock + safety_stock
    
    # Current inventory position (on-hand + weighted pipeline)
    current_inv_position = on_hand_inventory + weighted_pipeline
    
    # Calculate order gap
    order_gap = target_inv_level - current_inv_position
    
    # Apply smoothed ordering with constraints
    if order_gap > 0:
        # Use power function for order smoothing
        smoothed_order = order_gap ** order_aggressiveness
        # Apply min/max constraints and round to integer
        order_amount = max(min_order_qty, min(max_order_qty, int(smoothed_order)))
    else:
        order_amount = 0
    
    return order_amount
