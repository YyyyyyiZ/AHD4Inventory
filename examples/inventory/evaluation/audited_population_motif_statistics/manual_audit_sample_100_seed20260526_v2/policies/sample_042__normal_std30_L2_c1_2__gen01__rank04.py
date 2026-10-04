# sample_id: 042
# folder: deepseek-chat_normal_std30_L2_c1_2_50_plain_processed_scipy_15_default_e1-e2-m2_4_r1
# distribution: normal_std30_L2_c1_2
# generation: 1
# rank_in_population_file: 4
# objective: 2318.88
# test_objective: 2265.944
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Base stock level
    base_stock = 303.7139198304675  # OPT_PARAM: {"initial": 303.7139198304675, "min": 100, "max": 500, "type": "float"}
    
    # Safety stock multiplier
    safety_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.5, "type": "float"}
    
    # Order smoothing factor (0-1, higher = more smoothing)
    smoothing_factor = 0.5672492181352733  # OPT_PARAM: {"initial": 0.5672492181352733, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Pipeline imbalance threshold
    imbalance_threshold = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Pipeline weight for inventory position calculation
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    
    # Calculate weighted inventory position
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + weighted_pipeline
    
    # Calculate average pipeline order (excluding current arrival)
    if len(pipeline_orders) > 1:
        future_pipeline = pipeline_orders[1:]  # Exclude q_{t,1} which arrives now
        avg_future = sum(future_pipeline) / len(future_pipeline)
    else:
        avg_future = 0
    
    # Detect pipeline imbalance
    pipeline_imbalance = False
    if len(pipeline_orders) >= 2 and avg_future > 0:
        immediate_coverage = sum(pipeline_orders[:min(2, len(pipeline_orders))])
        if immediate_coverage < avg_future * (1 - imbalance_threshold):
            pipeline_imbalance = True
    
    # Calculate safety stock
    if len(pipeline_orders) > 0:
        pipeline_variance = max(pipeline_orders) - min(pipeline_orders) if len(pipeline_orders) > 1 else 0
        safety_stock = safety_multiplier * (avg_future + pipeline_variance * 0.1)
    else:
        safety_stock = safety_multiplier * base_stock * 0.1
    
    # Determine target inventory position
    if pipeline_imbalance:
        target_position = base_stock + safety_stock * 1.5
    else:
        target_position = base_stock + safety_stock
    
    # Calculate raw order needed
    raw_order_needed = target_position - inventory_position
    
    # Apply smoothing: order a smoothed version of what's needed
    if raw_order_needed > 0:
        order_amount = raw_order_needed * smoothing_factor
    else:
        order_amount = 0
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
