# policy_hash: 998fc696e534b9f1bbbc7c3c57f4be1ec3f6df47c9cf41c42dfe87af501c8e26
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6011.46
# best_prompt_performance: 6011.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223844.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 180.719158296008  # OPT_PARAM: {"initial": 180.719158296008, "min": 100, "max": 350, "type": "float"}
    safety_multiplier = 0.9703126517944165  # OPT_PARAM: {"initial": 0.9703126517944165, "min": 0.5, "max": 2.5, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.5364581275679173  # OPT_PARAM: {"initial": 0.5364581275679173, "min": 0.3, "max": 0.9, "type": "float"}
    min_order_threshold = 15.1  # OPT_PARAM: {"initial": 15.1, "min": 5.0, "max": 50.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted sum with more weight on recent orders)
    effective_pipeline = 0
    if pipeline_orders:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]  # Normalize
        effective_pipeline = sum(w * p for w, p in zip(weights, reversed(pipeline_orders)))

    # Calculate target inventory position with safety stock
    safety_stock = safety_multiplier * (effective_pipeline if effective_pipeline > 0 else base_stock * 0.3)
    target_inventory = base_stock + safety_stock

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing to avoid extreme fluctuations
    if abs(order_needed) > base_stock * 0.4:
        smoothed_order = order_needed * smoothing_factor
    else:
        smoothed_order = order_needed

    # Apply minimum order threshold to reduce small, frequent orders
    if 0 < smoothed_order < min_order_threshold:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
