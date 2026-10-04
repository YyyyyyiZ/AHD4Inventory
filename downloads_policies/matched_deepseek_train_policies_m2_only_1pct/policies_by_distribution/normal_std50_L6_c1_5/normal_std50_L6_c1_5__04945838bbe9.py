# policy_hash: 04945838bbe9e535c096b6a9546e93d19b9befaf2efa5447a85671f31acd50d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 50
# source_prompt_files: 1
# best_target_performance: 6456.52
# best_prompt_performance: 6456.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_135915.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 839.0746769298983  # OPT_PARAM: {"initial": 839.0746769298983, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 169.17467692989518  # OPT_PARAM: {"initial": 169.17467692989518, "min": 120, "max": 250, "type": "float"}
    smoothing_factor = 0.18983129338509375  # OPT_PARAM: {"initial": 0.18983129338509375, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    low_inventory_threshold = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.4, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order-up-to level
    desired_level = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, desired_level - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order

    # Ensure minimum order quantity when inventory is low
    if inventory_position < desired_level * low_inventory_threshold:
        order_amount = max(min_order, smoothed_order)
    else:
        order_amount = smoothed_order

    return order_amount
