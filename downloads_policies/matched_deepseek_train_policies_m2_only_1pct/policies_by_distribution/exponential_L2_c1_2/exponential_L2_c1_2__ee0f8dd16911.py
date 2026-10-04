# policy_hash: ee0f8dd16911f46f7cafeb371b986e991aa57226dd0ac98be6d796f7e233be35
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5912.72
# best_prompt_performance: 5912.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225107.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 188.10411163689452  # OPT_PARAM: {"initial": 188.10411163689452, "min": 150, "max": 350, "type": "float"}
    safety_multiplier = 1.2424827661631734  # OPT_PARAM: {"initial": 1.2424827661631734, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 0.92  # OPT_PARAM: {"initial": 0.92, "min": 0.7, "max": 1.2, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    min_order_threshold = 24.998076842089603  # OPT_PARAM: {"initial": 24.998076842089603, "min": 10.0, "max": 50.0, "type": "float"}
    demand_estimate_factor = 0.7534280113238188  # OPT_PARAM: {"initial": 0.7534280113238188, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline for better lead time coverage
    effective_pipeline = 0
    if pipeline_orders:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]
        effective_pipeline = sum(w * p for w, p in zip(weights, pipeline_orders))

    # Estimate expected demand based on pipeline and base stock
    expected_demand = demand_estimate_factor * (base_stock * 0.5 + effective_pipeline * 0.5)

    # Calculate safety stock with demand consideration
    safety_stock = safety_multiplier * expected_demand

    # Target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing based on magnitude
    if abs(order_needed) > base_stock * 0.3:
        smoothed_order = order_needed * smoothing_factor
    else:
        smoothed_order = order_needed

    # Apply minimum order threshold
    if 0 < smoothed_order < min_order_threshold:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
