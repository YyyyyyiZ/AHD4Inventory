# policy_hash: 34f5b0dd54d11fc01525a202790e7eb094572db989d911b1dc50c29d0ea6e637
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1328.28
# best_prompt_performance: 1328.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030556.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 307.5384666461468  # OPT_PARAM: {"initial": 307.5384666461468, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 48.65698516466578  # OPT_PARAM: {"initial": 48.65698516466578, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.5834054175130069  # OPT_PARAM: {"initial": 0.5834054175130069, "min": 0.1, "max": 1.5, "type": "float"}
    demand_buffer = 19.641696225833634  # OPT_PARAM: {"initial": 19.641696225833634, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0, "max": 1, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected short-term demand from pipeline
    # More weight to recent orders in pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(reversed(pipeline_orders)))
    if weighted_pipeline > 0:
        pipeline_ratio = weighted_pipeline / sum(pipeline_orders)
    else:
        pipeline_ratio = 1.0

    # Dynamic order-up-to level based on pipeline activity
    dynamic_adjustment = demand_buffer * pipeline_ratio
    order_up_to = base_stock + safety_stock + dynamic_adjustment

    # Calculate order amount with adjustment
    raw_order = max(0, order_up_to - inventory_position)

    # Apply adjustment factor to smooth ordering
    adjusted_order = raw_order * adjustment_factor

    # Round to nearest integer (since order amount must be integer)
    order_amount = int(round(adjusted_order))

    return order_amount
