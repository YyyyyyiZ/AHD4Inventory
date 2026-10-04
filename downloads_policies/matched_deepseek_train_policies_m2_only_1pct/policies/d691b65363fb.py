# policy_hash: d691b65363fbd50d76c77b0575133f3bf40107ab40401016c6962bd59d804acb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1173.52
# best_prompt_performance: 1173.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_084455.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 581.3650422292188  # OPT_PARAM: {"initial": 581.3650422292188, "min": 400, "max": 900, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast_window = 5  # OPT_PARAM: {"initial": 5, "min": 1, "max": 10, "type": "int"}
    forecast_smoothing = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.9, "type": "float"}
    order_smoothing = 0.8960376448640792  # OPT_PARAM: {"initial": 0.8960376448640792, "min": 0.1, "max": 0.9, "type": "float"}
    forecast_adjustment = 1.318896734981764  # OPT_PARAM: {"initial": 1.318896734981764, "min": 0.1, "max": 2.0, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 400, "type": "float"}
    min_order = 89.37949791721317  # OPT_PARAM: {"initial": 89.37949791721317, "min": 0, "max": 100, "type": "float"}
    lead_time_buffer = 0.9760415568682096  # OPT_PARAM: {"initial": 0.9760415568682096, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using exponential smoothing with longer window
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

    # Adjust base stock based on demand forecast and lead time
    adjusted_base_stock = base_stock + forecast_adjustment * forecast * lead_time_buffer

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, base_stock * 0.8 + safety_stock)

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Smooth ordering with minimum order constraint
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * last_order
        order_amount = max(min_order, int(round(smoothed_order)))
    else:
        order_amount = max(min_order, int(round(raw_order)))

    # Limit maximum order size
    order_amount = min(order_amount, max_order)

    return order_amount
