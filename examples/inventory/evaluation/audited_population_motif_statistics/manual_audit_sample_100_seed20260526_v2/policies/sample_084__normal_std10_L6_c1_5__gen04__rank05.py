# sample_id: 084
# folder: deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r6
# distribution: normal_std10_L6_c1_5
# generation: 4
# rank_in_population_file: 5
# objective: 1365.78
# test_objective: 1344.857
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 585.6428063424911  # OPT_PARAM: {"initial": 585.6428063424911, "min": 450, "max": 700, "type": "float"}
    safety_stock = 107.01607779666783  # OPT_PARAM: {"initial": 107.01607779666783, "min": 40, "max": 120, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.9, "type": "float"}
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 3.0, "type": "float"}
    min_order = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 10, "max": 50, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate demand estimate using weighted average of recent pipeline orders
    if len(pipeline_orders) > 0:
        # Simple exponential weighting: recent orders get more weight
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]  # Normalize
        demand_estimate = sum(w * q for w, q in zip(weights, pipeline_orders))
    else:
        demand_estimate = 100.0
    
    # Adjust base stock based on demand estimate
    adjusted_base = base_stock + (demand_estimate - 100) * demand_adjustment
    
    # Calculate target inventory position
    target_position = adjusted_base + safety_stock
    
    # Calculate order needed
    order_needed = target_position - inventory_position
    
    # Apply smoothing to reduce order volatility
    if order_needed > min_order:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_estimate
    else:
        smoothed_order = max(0, order_needed)
    
    # Round to integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))
    
    return order_amount
