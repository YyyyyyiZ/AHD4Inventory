# policy_hash: a09ca520ca43dc3755f4e2ce5ddb9a0ae76183052508a7c6645b88b39726364d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1214.98
# best_prompt_performance: 1215.26
# best_rel_error_pct: 0.023046
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_035737.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 303.3838411703085  # OPT_PARAM: {"initial": 303.3838411703085, "min": 100, "max": 500, "type": "float"}
    safety_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.5, "type": "float"}
    smoothing_factor = 0.27945096664540847  # OPT_PARAM: {"initial": 0.27945096664540847, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_std = max(1.0, (max(pipeline_orders) - min(pipeline_orders)) / 2.0)
    else:
        pipeline_std = 0.0

    # Adjust target based on pipeline status and demand anticipation
    safety_stock = safety_factor * pipeline_std
    target_level = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    raw_order = max(0, target_level - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1] if pipeline_orders else raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
