# policy_hash: 1b5e67850430bd41bbec317d50a38cf3530dd266187e076892f683e03a9de3f2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1274.42
# best_prompt_performance: 1273.36
# best_rel_error_pct: 0.083175
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_094341.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 357.55974452384294  # OPT_PARAM: {"initial": 357.55974452384294, "min": 200, "max": 400, "type": "float"}
    pipeline_weight = 0.5259692308492718  # OPT_PARAM: {"initial": 0.5259692308492718, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 20, "type": "int"}

    # Calculate effective inventory position with pipeline weighting
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Base stock policy with smoothing
    raw_order = base_stock - inventory_position
    order_amount = max(min_order, raw_order)

    # Apply exponential smoothing to reduce order volatility
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * min_order
        order_amount = max(min_order, smoothed_order)

    return order_amount
