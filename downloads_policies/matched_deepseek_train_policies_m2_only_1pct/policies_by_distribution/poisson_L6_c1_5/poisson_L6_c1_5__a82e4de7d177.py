# policy_hash: a82e4de7d17772b5aad4c197b50ea929a7e916032243344e1baf19be44016947
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1176.1
# best_prompt_performance: 1176.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_075136.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 707.8535092378305  # OPT_PARAM: {"initial": 707.8535092378305, "min": 400, "max": 900, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast_window = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 10, "type": "int"}
    forecast_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.9, "type": "float"}
    order_smoothing = 0.678620193268805  # OPT_PARAM: {"initial": 0.678620193268805, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using exponential smoothing of pipeline orders
    # Use pipeline orders as proxy for recent demand (since orders follow demand)
    if len(pipeline_orders) > 0:
        # Take recent pipeline orders as demand proxy
        window = min(demand_forecast_window, len(pipeline_orders))
        recent_orders = pipeline_orders[-window:]

        # Simple exponential smoothing
        forecast = sum(recent_orders) / window
        if len(pipeline_orders) >= 2:
            # Apply smoothing to reduce noise
            prev_forecast = sum(pipeline_orders[-window-1:-1]) / window if len(pipeline_orders) > window else forecast
            forecast = forecast_smoothing * forecast + (1 - forecast_smoothing) * prev_forecast
    else:
        forecast = 100.0  # Default estimate

    # Adjust base stock based on demand forecast
    # Higher forecast → higher base stock, but with diminishing returns
    forecast_adjustment = 0.9826555744630007  # OPT_PARAM: {"initial": 0.9826555744630007, "min": 0.1, "max": 2.0, "type": "float"}
    adjusted_base_stock = base_stock + forecast_adjustment

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, base_stock * 0.8 + safety_stock)

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Smooth ordering: blend with previous order to avoid extreme fluctuations
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * last_order
        # Ensure order is integer and non-negative
        order_amount = max(0, int(round(smoothed_order)))
    else:
        order_amount = max(0, int(round(raw_order)))

    # Additional smoothing: limit maximum order size
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 400, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
