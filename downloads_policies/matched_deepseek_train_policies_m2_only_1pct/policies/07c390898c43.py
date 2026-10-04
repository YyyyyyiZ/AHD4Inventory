# policy_hash: 07c390898c4368f77038153f67ddbf28ff622e3264d6d4bf2d149b30b672af14
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 33
# source_prompt_files: 2
# best_target_performance: 11027.99
# best_prompt_performance: 11027.99
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084729.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 402.27628826891424  # OPT_PARAM: {"initial": 402.27628826891424, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 9.001017100385695  # OPT_PARAM: {"initial": 9.001017100385695, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.24021449576766435  # OPT_PARAM: {"initial": 0.24021449576766435, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals (simplified forecast)
    # Use average of recent pipeline arrivals as demand indicator
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        forecast_adjustment = avg_pipeline * demand_forecast_factor
    else:
        forecast_adjustment = 0

    # Dynamic base stock level
    dynamic_base = base_stock + safety_stock + forecast_adjustment

    # Calculate order amount
    order_amount = max(0, dynamic_base - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        # Consider recent order patterns
        recent_order_avg = sum(pipeline_orders[-2:]) / min(2, len(pipeline_orders))
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order_avg
        order_amount = max(0, smoothed_order)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
