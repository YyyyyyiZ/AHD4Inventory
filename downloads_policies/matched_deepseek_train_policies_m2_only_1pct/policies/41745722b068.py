# policy_hash: 41745722b068a559d257d176d675dfc0624f0ac6f94f1ed357b90d8addf71004
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 5902.72
# best_prompt_performance: 5902.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225200.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 191.40765768426223  # OPT_PARAM: {"initial": 191.40765768426223, "min": 180, "max": 280, "type": "float"}
    safety_multiplier = 0.9180541520957991  # OPT_PARAM: {"initial": 0.9180541520957991, "min": 0.9, "max": 1.3, "type": "float"}
    pipeline_coverage = 0.9658764956777677  # OPT_PARAM: {"initial": 0.9658764956777677, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    min_order_threshold = 18.97557244954027  # OPT_PARAM: {"initial": 18.97557244954027, "min": 5.0, "max": 30.0, "type": "float"}
    demand_estimate_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    cost_ratio_weight = 0.2543133321698389  # OPT_PARAM: {"initial": 0.2543133321698389, "min": 0.2, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple pipeline coverage (no complex weighting)
    covered_pipeline = pipeline_coverage * sum(pipeline_orders)

    # Estimate expected demand based on base stock
    expected_demand = demand_estimate_factor * base_stock

    # Adjust safety stock based on cost ratio (p=2, h=1)
    # Higher weight on avoiding lost sales
    safety_stock = safety_multiplier * expected_demand * (1 + cost_ratio_weight)

    # Target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order needed
    order_needed = target_inventory - (on_hand_inventory + covered_pipeline)

    # Apply smoothing
    smoothed_order = order_needed * smoothing_factor

    # Apply minimum order threshold
    if 0 < smoothed_order < min_order_threshold:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
