# policy_hash: a94b096fc06f1452f92a2ea099ffbf112fd6de3d88b331491c47406548260763
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1836.15
# best_prompt_performance: 1849.4
# best_rel_error_pct: 0.721619
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060208.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 545.2187476228391  # OPT_PARAM: {"initial": 545.2187476228391, "min": 400, "max": 800, "type": "float"}
    safety_stock = 62.77959529025239  # OPT_PARAM: {"initial": 62.77959529025239, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.15795038832302608  # OPT_PARAM: {"initial": 0.15795038832302608, "min": 0.15, "max": 0.4, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}
    demand_forecast_factor = 0.9817241859324333  # OPT_PARAM: {"initial": 0.9817241859324333, "min": 0.8, "max": 1.3, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    pipeline_weight = 0.9058958167016642  # OPT_PARAM: {"initial": 0.9058958167016642, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Weighted pipeline adjustment - give more weight to recent orders
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight

    # Normalize weighted pipeline to get demand estimate
    if len(pipeline_orders) > 0:
        weight_sum = sum(pipeline_weight ** i for i in range(len(pipeline_orders)))
        avg_weighted_demand = weighted_pipeline / weight_sum
    else:
        avg_weighted_demand = 0

    # Forecast adjustment based on weighted demand
    forecast_adjustment = avg_weighted_demand * demand_forecast_factor * lead_time

    # Dynamic target inventory
    target_inventory = base_stock + safety_stock + forecast_adjustment

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with minimum order threshold
    if order_needed > min_order_threshold:
        order_amount = smoothing_factor * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
