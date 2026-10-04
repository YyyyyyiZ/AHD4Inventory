# policy_hash: 26b627c70f7459f8a79cabe6868e2448507fe0fb5856f9a80923aaceae81c2eb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 6502.6
# best_prompt_performance: 6501.18
# best_rel_error_pct: 0.021837
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235853.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 224.0524151550647  # OPT_PARAM: {"initial": 224.0524151550647, "min": 100, "max": 400, "type": "float"}
    safety_stock = 19.05241515506444  # OPT_PARAM: {"initial": 19.05241515506444, "min": 0, "max": 50, "type": "float"}
    pipeline_weight = 0.8781794930084694  # OPT_PARAM: {"initial": 0.8781794930084694, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target based on pipeline variability
    pipeline_std = 0.0
    if len(pipeline_orders) > 1:
        mean_pl = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((x - mean_pl) ** 2 for x in pipeline_orders) / len(pipeline_orders)) ** 0.5

    # Adjust target based on pipeline variability
    variability_adjustment = demand_buffer * pipeline_std
    target_inventory = base_stock + safety_stock + variability_adjustment

    # Calculate base order
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with recent pipeline trend
    if pipeline_orders:
        recent_trend = pipeline_orders[-1] if pipeline_orders else 0
        smoothed_order = smoothing_factor * base_order + (1 - smoothing_factor) * recent_trend
    else:
        smoothed_order = base_order

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
