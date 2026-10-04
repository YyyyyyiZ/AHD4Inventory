# policy_hash: 1adeffd084d087e7a61ec044acd122ddfab45991b03e742ac595dd81c0d5a836
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 3924.05
# best_prompt_performance: 3923.9
# best_rel_error_pct: 0.003823
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_175755.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 325.724799208634  # OPT_PARAM: {"initial": 325.724799208634, "min": 200, "max": 400, "type": "float"}
    safety_stock = 40.724799208635346  # OPT_PARAM: {"initial": 40.724799208635346, "min": 20, "max": 60, "type": "float"}
    pipeline_coverage = 0.6530705792956156  # OPT_PARAM: {"initial": 0.6530705792956156, "min": 0.4, "max": 0.8, "type": "float"}
    demand_estimate = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 130, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage

    # Target inventory calculation
    target_inventory = base_stock + safety_stock + effective_pipeline

    # Calculate order amount
    gap = target_inventory - inventory_position
    if gap > 0:
        # Use demand estimate with multiplier for more responsive ordering
        max_order = order_multiplier * demand_estimate
        order_amount = min(gap, max_order)
    else:
        order_amount = 0

    return order_amount
