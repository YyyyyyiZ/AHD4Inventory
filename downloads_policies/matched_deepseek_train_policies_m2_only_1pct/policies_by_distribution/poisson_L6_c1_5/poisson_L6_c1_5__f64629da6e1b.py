# policy_hash: f64629da6e1b5a7c355c22865bc26f225a448c95a008ab86328156edd9c8a248
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 1175.74
# best_prompt_performance: 1175.7
# best_rel_error_pct: 0.003402
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_080430.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 599.2385791598424  # OPT_PARAM: {"initial": 599.2385791598424, "min": 400, "max": 900, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 10, "type": "int"}
    forecast_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    order_smoothing = 0.8979716283101568  # OPT_PARAM: {"initial": 0.8979716283101568, "min": 0.1, "max": 0.9, "type": "float"}
    forecast_adjustment = 1.1213836618288429  # OPT_PARAM: {"initial": 1.1213836618288429, "min": 0.1, "max": 2.0, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 400, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using exponential smoothing
    if len(pipeline_orders) > 0:
        window = min(demand_forecast_window, len(pipeline_orders))
        recent_orders = pipeline_orders[-window:]
        forecast = sum(recent_orders) / window

        if len(pipeline_orders) >= 2 and window > 1:
            prev_orders = pipeline_orders[-window-1:-1] if len(pipeline_orders) > window else recent_orders
            prev_forecast = sum(prev_orders) / window
            forecast = forecast_smoothing * forecast + (1 - forecast_smoothing) * prev_forecast
    else:
        forecast = 100.0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + forecast_adjustment * forecast

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, base_stock * 0.8 + safety_stock)

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Smooth ordering
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * last_order
        order_amount = max(0, int(round(smoothed_order)))
    else:
        order_amount = max(0, int(round(raw_order)))

    # Limit maximum order size
    order_amount = min(order_amount, max_order)

    return order_amount
