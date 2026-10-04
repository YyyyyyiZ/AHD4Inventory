# policy_hash: 775dc47936323312757ed79a65bc55f9dd0fe0156eb9e0678b27bf529400109e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 3299.1
# best_prompt_performance: 3301.78
# best_rel_error_pct: 0.081234
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_023749.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 618.9904121162426  # OPT_PARAM: {"initial": 618.9904121162426, "min": 400, "max": 800, "type": "float"}
    safety_stock = 78.9904121162423  # OPT_PARAM: {"initial": 78.9904121162423, "min": 20, "max": 150, "type": "float"}
    demand_forecast_factor = 0.6757617371944419  # OPT_PARAM: {"initial": 0.6757617371944419, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.11981890339985152  # OPT_PARAM: {"initial": 0.11981890339985152, "min": 0.0, "max": 0.3, "type": "float"}
    smoothing_factor = 0.4498214970913999  # OPT_PARAM: {"initial": 0.4498214970913999, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Adjust target based on pipeline status
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_weight * avg_pipeline
    adjusted_target = target_inventory - pipeline_adjustment

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = base_order * smoothing_factor

    # Apply demand forecast factor
    order_amount = int(round(smoothed_order * demand_forecast_factor))

    return order_amount
