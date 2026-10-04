# policy_hash: 9802ece4d61f63fed23dea426c9016d48f2d7bad2bfdacc5c6e384e9ede8ec37
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 58
# source_prompt_files: 1
# best_target_performance: 4007.0
# best_prompt_performance: 4007.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_063509.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 744.2412150075289  # OPT_PARAM: {"initial": 744.2412150075289, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 71.53574682295528  # OPT_PARAM: {"initial": 71.53574682295528, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 103.03090689765898  # OPT_PARAM: {"initial": 103.03090689765898, "min": 70, "max": 150, "type": "float"}
    pipeline_weight = 0.5589413389979382  # OPT_PARAM: {"initial": 0.5589413389979382, "min": 0.0, "max": 1.0, "type": "float"}
    order_smoothing = 0.112010674195196  # OPT_PARAM: {"initial": 0.112010674195196, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline for adjustment
    weighted_pipeline = 0.0
    total_pipeline = 0.0
    for i, p in enumerate(pipeline_orders):
        weight = pipeline_weight ** i
        weighted_pipeline += p * weight
        total_pipeline += p

    # Simple pipeline adjustment factor
    if total_pipeline > 0:
        pipeline_factor = weighted_pipeline / total_pipeline
    else:
        pipeline_factor = 1.0

    # Target inventory position
    target = base_stock * pipeline_factor + safety_stock

    # Calculate desired order
    desired_order = max(0, target - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    smoothed_order = order_smoothing * desired_order + (1 - order_smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
