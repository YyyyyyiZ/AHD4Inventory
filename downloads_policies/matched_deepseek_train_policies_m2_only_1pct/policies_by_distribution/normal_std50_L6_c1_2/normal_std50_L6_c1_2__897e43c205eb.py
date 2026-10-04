# policy_hash: 897e43c205eb5ae704a33ab9b021292faa65dcc4d5a8ae7762a563fd0b1c92f1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 3885.19
# best_prompt_performance: 3884.78
# best_rel_error_pct: 0.010553
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_234011.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 373.3058266035579  # OPT_PARAM: {"initial": 373.3058266035579, "min": 100, "max": 600, "type": "float"}
    safety_stock = 103.40582660356432  # OPT_PARAM: {"initial": 103.40582660356432, "min": 30, "max": 200, "type": "float"}
    demand_forecast_factor = 1.0717868891811617  # OPT_PARAM: {"initial": 1.0717868891811617, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use more recent orders (last 3 periods) for demand forecasting
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        expected_demand = sum(recent_orders) / len(recent_orders)
    else:
        expected_demand = 0

    # Adjust base stock based on expected demand
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * demand_forecast_factor)

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with expected demand
    smoothed_order = raw_order * smoothing_factor + (1 - smoothing_factor) * expected_demand

    # Ensure order is non-negative integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
