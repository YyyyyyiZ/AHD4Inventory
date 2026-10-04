# policy_hash: 54e1353b175ca5e5953ef447a09c5f184225fe8a0bf67a9d69ed55a30dca790e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4572.72
# best_prompt_performance: 4616.91
# best_rel_error_pct: 0.966383
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_123759.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 726.70291644994  # OPT_PARAM: {"initial": 726.70291644994, "min": 600, "max": 750, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 120, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    lost_sales_penalty_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.1, "max": 1.5, "type": "float"}
    min_order_threshold = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 10.0, "max": 40.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline (more weight on near-term arrivals)
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Simple base stock adjustment based on pipeline coverage
    pipeline_coverage = weighted_pipeline / (base_stock + 1e-6)
    adjusted_base = base_stock * (1 - demand_forecast_factor * min(1.0, pipeline_coverage))

    # Calculate desired order-up-to level
    desired_level = adjusted_base + safety_stock * lost_sales_penalty_factor

    # Calculate order amount with smoothing
    raw_order = desired_level - inventory_position
    smoothed_order = smoothing_factor * raw_order

    # Apply minimum order threshold
    if smoothed_order > 0 and smoothed_order < min_order_threshold:
        order_amount = min_order_threshold
    else:
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
