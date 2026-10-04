# policy_hash: a5d2ff50e9a7d2a5ac4f84e6ebe1854bfeaec9b913c1ded0dc1572f05ff271fd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 6167.72
# best_prompt_performance: 6167.7
# best_rel_error_pct: 0.000324
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041303.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.6246420134992  # OPT_PARAM: {"initial": 283.6246420134992, "min": 150, "max": 400, "type": "float"}
    demand_window = 8  # OPT_PARAM: {"initial": 8, "min": 3, "max": 15, "type": "int"}
    safety_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.8, "max": 2.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    forecast_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    min_order = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders if pipeline_orders else [0]

    # Simple moving average forecast
    avg_forecast = sum(recent_arrivals) / len(recent_arrivals)

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 2:
        demand_variance = sum((r - avg_forecast) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * avg_forecast * 0.5

    # Adjust base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Consider pipeline content
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock + forecast_weight * avg_forecast - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * avg_forecast

    # Round and ensure minimum order if positive
    if smoothed_order > 0:
        order_amount = int(round(max(min_order, smoothed_order)))
    else:
        order_amount = 0

    return order_amount
