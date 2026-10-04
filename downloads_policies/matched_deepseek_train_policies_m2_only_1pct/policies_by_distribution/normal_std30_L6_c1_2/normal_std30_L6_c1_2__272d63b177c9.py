# policy_hash: 272d63b177c96f421a136b6859351df9a4c814bf89fef315508317acbac0f2d6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 3171.1
# best_prompt_performance: 3166.24
# best_rel_error_pct: 0.153259
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_025557.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 476.5944774239229  # OPT_PARAM: {"initial": 476.5944774239229, "min": 400, "max": 700, "type": "float"}
    safety_stock = 61.82704868429557  # OPT_PARAM: {"initial": 61.82704868429557, "min": 30, "max": 150, "type": "float"}
    pipeline_coverage = 0.539333431447915  # OPT_PARAM: {"initial": 0.539333431447915, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.26742873962499725  # OPT_PARAM: {"initial": 0.26742873962499725, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with discounted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target order-up-to level
    target_level = base_stock + safety_stock

    # Raw order needed to reach target
    raw_order_needed = max(0, target_level - inventory_position)

    # Apply exponential smoothing to reduce order volatility
    smoothed_order = smoothing_factor * raw_order_needed

    # Round to nearest integer for practical implementation
    order_amount = int(round(smoothed_order))

    return order_amount
