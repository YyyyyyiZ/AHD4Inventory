# sample_id: 024
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_8_r6
# distribution: poisson_L6_c1_2
# generation: 3
# rank_in_population_file: 6
# objective: 781.98108
# test_objective: 757.94413
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 69.29783740818819  # OPT_PARAM: {"initial": 69.29783740818819, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 50, "max": 150, "type": "float"}
    max_order = 95.00028797791165  # OPT_PARAM: {"initial": 95.00028797791165, "min": 50, "max": 500, "type": "float"}
    smoothing_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    
    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)
    
    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * raw_order
    
    # Cap order amount to avoid excessive ordering
    order_amount = min(smoothed_order, max_order)
    
    return order_amount
