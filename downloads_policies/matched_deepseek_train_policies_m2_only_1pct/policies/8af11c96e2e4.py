# policy_hash: 8af11c96e2e4efc622a10363be67610a6c4757bdd4b2d75515dbc330419b7e8b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 5938.62
# best_prompt_performance: 5938.6
# best_rel_error_pct: 0.000337
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024216.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 147.6152318583714  # OPT_PARAM: {"initial": 147.6152318583714, "min": 50, "max": 300, "type": "float"}
    safety_stock = 67.61523185837139  # OPT_PARAM: {"initial": 67.61523185837139, "min": 20, "max": 150, "type": "float"}
    demand_forecast_factor = 0.088756669466929  # OPT_PARAM: {"initial": 0.088756669466929, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based only on most recent arrival
    if len(pipeline_orders) >= 1 and pipeline_orders[0] > 0:
        forecast_adjustment = demand_forecast_factor * pipeline_orders[0]
    else:
        forecast_adjustment = 0

    # Dynamic base stock level
    dynamic_base = base_stock + safety_stock + forecast_adjustment

    # Calculate order amount
    order_amount = max(0, dynamic_base - inventory_position)

    # Apply stronger smoothing to reduce volatility
    smoothing_factor = 0.17006908795208336  # OPT_PARAM: {"initial": 0.17006908795208336, "min": 0.1, "max": 0.5, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
