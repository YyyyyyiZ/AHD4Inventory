# policy_hash: 7fe98e9d6bf7edc9e9e0eaf32f7d2a7fb8c3cb2385ce37a7cd3d2ce98e3a6e7f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 2085.78
# best_prompt_performance: 2083.68
# best_rel_error_pct: 0.100682
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_084002.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 648.7090908993091  # OPT_PARAM: {"initial": 648.7090908993091, "min": 600, "max": 750, "type": "float"}
    safety_stock = 38.709090899308606  # OPT_PARAM: {"initial": 38.709090899308606, "min": 20, "max": 60, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 18.709090899308606  # OPT_PARAM: {"initial": 18.709090899308606, "min": 10, "max": 30, "type": "float"}
    pipeline_threshold = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 110, "type": "float"}
    adjustment_strength = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.6, "max": 1.0, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 20, "type": "int"}
    max_order = 150  # OPT_PARAM: {"initial": 150, "min": 100, "max": 200, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate average pipeline order
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
    else:
        avg_pipeline = 0

    # Adjust base stock based on pipeline level
    if avg_pipeline > pipeline_threshold:
        adjustment = pipeline_weight * adjustment_strength
    else:
        adjustment = 1.0

    # Target inventory position
    target_position = base_stock + safety_stock + demand_buffer

    # Calculate order amount with adjustment
    order_amount = max(0, (target_position - inventory_position) * adjustment)

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
