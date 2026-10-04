# policy_hash: fae8ea0027e8e130bf0418700e9f3fa80f859f4dbfa6d9ed427c24d56b950442
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 1198.44
# best_prompt_performance: 1198.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_000439.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 292.7494133043477  # OPT_PARAM: {"initial": 292.7494133043477, "min": 250, "max": 400, "type": "float"}
    safety_stock = 12.221494610201077  # OPT_PARAM: {"initial": 12.221494610201077, "min": 5, "max": 40, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3158851420194014  # OPT_PARAM: {"initial": 0.3158851420194014, "min": 0.2, "max": 0.8, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Base order calculation with safety stock
    order_amount = max(0, base_stock - effective_inventory + safety_stock)

    # Apply smoothing using most recent order if available
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
