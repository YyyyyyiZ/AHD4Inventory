# policy_hash: da3d8f09910baeac32cdf6081491dc689798a45a01d78133d3bc2bba7469d4c5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1462.78
# best_prompt_performance: 1468.2
# best_rel_error_pct: 0.370527
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055446.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 726.7059007376247  # OPT_PARAM: {"initial": 726.7059007376247, "min": 600, "max": 900, "type": "float"}
    safety_stock = 139.59020291485103  # OPT_PARAM: {"initial": 139.59020291485103, "min": 80, "max": 180, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 4, "max": 8, "type": "int"}
    demand_forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.3, "max": 1.2, "type": "float"}
    min_order_threshold = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 5, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Forecast demand using more recent pipeline orders (last 4 periods)
    recent_orders = pipeline_orders[-4:] if len(pipeline_orders) >= 4 else pipeline_orders
    if recent_orders:
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 100.0  # Default estimate

    # Dynamic target inventory with forecast adjustment
    forecast_adjustment = avg_recent_demand * demand_forecast_factor * lead_time
    target_inventory = base_stock + safety_stock + forecast_adjustment

    # Calculate order needed to reach target
    order_needed = target_inventory - inventory_position

    # Apply smoothing with minimum order threshold
    if order_needed > min_order_threshold:
        order_amount = smoothing_factor * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
