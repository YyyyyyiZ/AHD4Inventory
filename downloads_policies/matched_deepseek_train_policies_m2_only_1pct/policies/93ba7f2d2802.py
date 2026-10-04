# policy_hash: 93ba7f2d28020455b837e1e65b5a2412b4c31535ca2766375acda0a640bd0f83
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 775.46
# best_prompt_performance: 775.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_004404.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 515.3579800422947  # OPT_PARAM: {"initial": 515.3579800422947, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.45417610673916814  # OPT_PARAM: {"initial": 0.45417610673916814, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.11813980552513743  # OPT_PARAM: {"initial": 0.11813980552513743, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders) / max(len(pipeline_orders), 1)
    pipeline_risk_factor = 0.2969386413012736  # OPT_PARAM: {"initial": 0.2969386413012736, "min": 0.01, "max": 1.0, "type": "float"}

    # Dynamic adjustment based on current pipeline
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    recent_pipeline = sum(pipeline_orders[-3:]) / min(3, len(pipeline_orders)) if pipeline_orders else 0

    # Calculate target inventory with dynamic adjustments
    adjusted_base = base_stock * (1 + pipeline_risk_factor)
    target_inventory = adjusted_base + safety_stock

    # Smooth ordering to reduce volatility
    order_needed = max(0, target_inventory - inventory_position)
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * avg_pipeline

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
