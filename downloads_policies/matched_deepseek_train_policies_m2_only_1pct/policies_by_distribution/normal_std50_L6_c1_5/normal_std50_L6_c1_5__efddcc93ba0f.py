# policy_hash: efddcc93ba0f96f3f183aa3f49b85004aba4edb61f8fc1a660a4de94251c7599
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 6492.93
# best_prompt_performance: 6492.93
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_135501.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 832.7216190975167  # OPT_PARAM: {"initial": 832.7216190975167, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 162.72161909756431  # OPT_PARAM: {"initial": 162.72161909756431, "min": 100, "max": 300, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lead_time = 6  # Fixed parameter, not optimized

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast based on pipeline orders (simple moving average)
    # Use only non-zero pipeline orders for forecasting
    non_zero_orders = [q for q in pipeline_orders if q > 0]
    if len(non_zero_orders) > 0:
        avg_pipeline = sum(non_zero_orders) / len(non_zero_orders)
    else:
        avg_pipeline = 100.0  # Default estimate

    # Adjust base stock based on recent demand pattern
    demand_adjustment = 0.21731508313629244  # OPT_PARAM: {"initial": 0.21731508313629244, "min": 0.1, "max": 0.5, "type": "float"}
    adjusted_base_stock = base_stock + demand_adjustment

    # Calculate desired order-up-to level
    desired_level = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, desired_level - inventory_position)

    # Apply smoothing with minimum order threshold
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}
    smoothed_order = smoothing_factor * raw_order

    # Ensure minimum order quantity when inventory is low
    if inventory_position < desired_level * 0.7:  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
        order_amount = max(min_order, smoothed_order)
    else:
        order_amount = smoothed_order

    return order_amount
