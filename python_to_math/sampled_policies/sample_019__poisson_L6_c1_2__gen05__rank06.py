# sample_id: 019
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_6_r6
# distribution: poisson_L6_c1_2
# generation: 5
# rank_in_population_file: 6
# objective: 1053.82
# test_objective: 1032.595
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;threshold_order_activation;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 630.0044857452867  # OPT_PARAM: {"initial": 630.0044857452867, "min": 550, "max": 700, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 25, "max": 55, "type": "float"}
    demand_forecast = 97.53915439102583  # OPT_PARAM: {"initial": 97.53915439102583, "min": 90, "max": 104, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.15, "type": "float"}
    order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 20, "type": "float"}
    cost_ratio_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.6, "max": 0.75, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_forecast * lead_time
    
    # Adjust safety stock based on cost ratio (p/(p+h) = 2/3 ≈ 0.667)
    adjusted_safety_stock = safety_stock * cost_ratio_factor
    
    # Calculate target inventory level with pipeline consideration
    # Give more weight to near-term pipeline arrivals
    pipeline_imbalance = sum(p * (1 - pipeline_weight * i) for i, p in enumerate(pipeline_orders)) / lead_time if lead_time > 0 else 0
    target_inventory = expected_lead_time_demand + adjusted_safety_stock - max(0, pipeline_imbalance - demand_forecast)
    
    # Use the maximum of base_stock and target_inventory as order-up-to level
    order_up_to = max(base_stock, target_inventory)
    
    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)
    
    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0
    
    # Apply order threshold to avoid small orders
    if smoothed_order < order_threshold:
        order_amount = 0
    else:
        order_amount = int(round(smoothed_order))
    
    return order_amount
