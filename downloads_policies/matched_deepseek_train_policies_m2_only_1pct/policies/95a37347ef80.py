# policy_hash: 95a37347ef80298454c7368c1235b799aada07e5f7bee46658a64847ae51bf1b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6123.24
# best_prompt_performance: 6123.3
# best_rel_error_pct: 0.000980
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041223.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.1751423845171  # OPT_PARAM: {"initial": 350.1751423845171, "min": 150, "max": 400, "type": "float"}
    demand_window = 8  # OPT_PARAM: {"initial": 8, "min": 4, "max": 15, "type": "int"}
    safety_factor = 1.933435753573328  # OPT_PARAM: {"initial": 1.933435753573328, "min": 1.5, "max": 3.5, "type": "float"}
    smoothing_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.15, "max": 0.8, "type": "float"}
    pipeline_weight = 0.30000000000042454  # OPT_PARAM: {"initial": 0.30000000000042454, "min": 0.3, "max": 0.9, "type": "float"}
    forecast_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    min_order = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 30, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline arrivals as demand proxy
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders if pipeline_orders else [0]

    # Calculate demand forecast using exponential smoothing
    if recent_arrivals:
        # Simple exponential smoothing forecast
        forecast = recent_arrivals[0]
        for arrival in recent_arrivals[1:]:
            forecast = forecast_weight * arrival + (1 - forecast_weight) * forecast
    else:
        forecast = base_stock * 0.2

    # Calculate safety stock based on demand variability
    if len(recent_arrivals) >= 3:
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
        demand_variance = sum((r - avg_demand) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5)
    else:
        safety_stock = safety_factor * forecast * 0.3

    # Adjust base stock with safety stock and forecast
    adjusted_base_stock = base_stock + safety_stock + forecast * 0.5

    # Consider pipeline content in target calculation
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * forecast

    # Ensure minimum order quantity and non-negative
    order_amount = int(round(max(min_order, smoothed_order)))

    return order_amount
