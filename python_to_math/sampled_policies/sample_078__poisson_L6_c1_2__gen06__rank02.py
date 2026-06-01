# sample_id: 078
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_8_r6
# distribution: poisson_L6_c1_2
# generation: 6
# rank_in_population_file: 2
# objective: 759.98
# test_objective: 745.637
# is_top10_by_distribution: True
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;state_dependent_target;partial_adjustment;order_clipping;order_smoothing
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.640380519374744  # OPT_PARAM: {"initial": 58.640380519374744, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 125.84085101407936  # OPT_PARAM: {"initial": 125.84085101407936, "min": 50, "max": 150, "type": "float"}
    max_order = 96.02075836350208  # OPT_PARAM: {"initial": 96.02075836350208, "min": 50, "max": 500, "type": "float"}
    smoothing_factor = 0.6628825194762518  # OPT_PARAM: {"initial": 0.6628825194762518, "min": 0.1, "max": 0.9, "type": "float"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    
    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock
    
    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)
    
    # Apply smoothing to reduce volatility
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * (pipeline_orders[-1] if pipeline_orders else 0)
    
    # Apply minimum order quantity to reduce small orders
    if smoothed_order > 0 and smoothed_order < min_order:
        smoothed_order = min_order
    
    # Cap order amount to avoid excessive ordering
    order_amount = min(smoothed_order, max_order)
    
    # Ensure non-negative integer
    order_amount = max(0, int(round(order_amount)))
    
    return order_amount
