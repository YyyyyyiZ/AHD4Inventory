# policy_hash: 524ea7cc5f4ddd39e2b07173272562c10878e535535d33842bc54ff8e655cb13
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5880.56
# best_prompt_performance: 5880.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225848.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 208.33230876336336  # OPT_PARAM: {"initial": 208.33230876336336, "min": 100, "max": 350, "type": "float"}
    safety_multiplier = 2.5691493229806373  # OPT_PARAM: {"initial": 2.5691493229806373, "min": 0.5, "max": 3.0, "type": "float"}
    smoothing_factor = 0.30000000000000004  # OPT_PARAM: {"initial": 0.30000000000000004, "min": 0.2, "max": 0.8, "type": "float"}
    pipeline_coverage = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    min_order = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 20, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from pipeline orders
    if len(pipeline_orders) >= 2:
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        variance = sum((p - mean_pipeline) ** 2 for p in pipeline_orders) / len(pipeline_orders)
        std_dev = variance ** 0.5
    else:
        std_dev = base_stock * 0.15

    # Safety stock based on demand variability
    safety_stock = safety_multiplier * std_dev

    # Adjust for pipeline coverage - simpler than historical policy
    pipeline_total = sum(pipeline_orders)
    expected_pipeline = base_stock * len(pipeline_orders) * pipeline_coverage
    pipeline_adjustment = max(0, expected_pipeline - pipeline_total) * 0.5

    # Target inventory position
    target_inventory = base_stock + safety_stock + pipeline_adjustment

    # Order needed with smoothing
    order_needed = target_inventory - inventory_position
    smoothed_order = order_needed * smoothing_factor

    # Apply minimum order constraint
    if smoothed_order > min_order:
        order_amount = max(min_order, int(round(smoothed_order)))
    else:
        order_amount = 0

    return order_amount
