# policy_hash: 07220cc366c4a3f2dd06875dab8616104fe0214f94a9fb4e4bd29de387d9d2e9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 6051.54
# best_prompt_performance: 6049.84
# best_rel_error_pct: 0.028092
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055204.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 285.0  # OPT_PARAM: {"initial": 285.0, "min": 200, "max": 350, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 70, "max": 130, "type": "float"}
    smoothing_factor = 0.46697589658602334  # OPT_PARAM: {"initial": 0.46697589658602334, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline coverage
    effective_pipeline = pipeline_weight * sum(pipeline_orders)

    # Adjust base stock based on cost ratio bias
    adjusted_base = base_stock * (lost_sales_weight / (1 + lost_sales_weight))

    # Calculate target inventory position
    target_inventory = adjusted_base + safety_stock - effective_pipeline

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure integer order amount
    order_amount = int(round(smoothed_order))

    return order_amount
