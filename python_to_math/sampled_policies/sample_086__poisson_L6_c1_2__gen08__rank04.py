# sample_id: 086
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r3
# distribution: poisson_L6_c1_2
# generation: 8
# rank_in_population_file: 4
# objective: 1163.24
# test_objective: 1163.609
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 920.0  # OPT_PARAM: {"initial": 920.0, "min": 850, "max": 1050, "type": "float"}
    safety_stock = 95.19999999999763  # OPT_PARAM: {"initial": 95.19999999999763, "min": 50, "max": 120, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.1, "max": 0.4, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    lost_sales_weight = 2.2  # OPT_PARAM: {"initial": 2.2, "min": 1.5, "max": 2.2, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 10, "type": "int"}
    max_order = 110  # OPT_PARAM: {"initial": 110, "min": 90, "max": 130, "type": "int"}
    
    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Adjust safety stock based on cost ratio
    adjusted_safety_stock = safety_stock * (lost_sales_weight / 2.0)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + adjusted_safety_stock
    
    # Apply base stock cap
    target_position = min(target_position, base_stock)
    
    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)
    
    # Apply smoothing to reduce order volatility
    smoothed_order = raw_order * smoothing_factor + (target_position - inventory_position) * (1 - smoothing_factor)
    
    # Apply pipeline weight to account for existing orders
    weighted_order = smoothed_order * pipeline_weight
    
    # Apply order limits
    if weighted_order > 0:
        weighted_order = max(min_order, min(weighted_order, max_order))
    
    # Round to nearest integer
    order_amount = int(round(weighted_order))
    
    return order_amount
