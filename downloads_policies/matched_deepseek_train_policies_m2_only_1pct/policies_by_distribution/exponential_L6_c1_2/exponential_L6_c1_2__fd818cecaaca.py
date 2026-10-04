# policy_hash: fd818cecaaca7ccd4241321c5cf7d62314f3cf58b3f522a5b079631e76f4c790
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 6067.54
# best_prompt_performance: 6068.12
# best_rel_error_pct: 0.009559
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_094645.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.2888533062711  # OPT_PARAM: {"initial": 451.2888533062711, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 0.8928336775114546  # OPT_PARAM: {"initial": 0.8928336775114546, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.16976138354048517  # OPT_PARAM: {"initial": 0.16976138354048517, "min": 0.15, "max": 0.4, "type": "float"}
    safety_stock = 101.28885330627149  # OPT_PARAM: {"initial": 101.28885330627149, "min": 50, "max": 150, "type": "float"}
    demand_buffer = 1.1423434881109225  # OPT_PARAM: {"initial": 1.1423434881109225, "min": 1.0, "max": 1.5, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based adjustment
    if raw_order > 0:
        # Simple demand adjustment based on recent arrivals
        if len(pipeline_orders) > 0 and pipeline_orders[0] > 0:
            demand_adjusted = raw_order * demand_buffer
            raw_order = min(demand_adjusted, raw_order * 1.3)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
