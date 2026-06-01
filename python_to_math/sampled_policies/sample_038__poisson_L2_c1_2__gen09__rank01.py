# sample_id: 038
# folder: deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6
# distribution: poisson_L2_c1_2
# generation: 9
# rank_in_population_file: 1
# objective: 758.44
# test_objective: 766.956
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 195.06472893772462  # OPT_PARAM: {"initial": 195.06472893772462, "min": 150, "max": 250, "type": "float"}
    safety_multiplier = 1.2008583079563495  # OPT_PARAM: {"initial": 1.2008583079563495, "min": 0.8, "max": 2.0, "type": "float"}
    smoothing_factor = 0.28326705351321924  # OPT_PARAM: {"initial": 0.28326705351321924, "min": 0.05, "max": 0.5, "type": "float"}
    lead_time_days = 2
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Use more accurate demand estimate based on historical data analysis
    demand_estimate = 100.13111443020748  # OPT_PARAM: {"initial": 100.13111443020748, "min": 90, "max": 110, "type": "float"}
    
    # Calculate safety stock with improved formula
    safety_stock = safety_multiplier * demand_estimate * (lead_time_days ** 0.5)
    
    # Adjust target based on pipeline composition - simplified
    pipeline_adjustment_factor = 0.7422589966119842  # OPT_PARAM: {"initial": 0.7422589966119842, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_adjustment = pipeline_adjustment_factor * sum(pipeline_orders)
    
    # Target inventory position with pipeline adjustment
    target = base_stock + safety_stock - pipeline_adjustment
    
    # Calculate raw order quantity
    raw_order = max(0, target - net_inventory)
    
    # Apply smoothing with minimum order threshold
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}
    
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_order
    else:
        smoothed_order = raw_order
    
    # Apply minimum order threshold
    if smoothed_order < min_order_threshold:
        smoothed_order = 0
    
    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    
    return order_amount
