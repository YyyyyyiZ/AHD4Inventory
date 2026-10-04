# policy_hash: cebc6f12126f9950c98faf2846f93280a04485426fae677fb9533b7217a96850
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6158.22
# best_prompt_performance: 6158.14
# best_rel_error_pct: 0.001299
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040638.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 272.20000000745733  # OPT_PARAM: {"initial": 272.20000000745733, "min": 100, "max": 800, "type": "float"}
    demand_forecast_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 10, "type": "int"}
    safety_multiplier = 1.0000000001006608  # OPT_PARAM: {"initial": 1.0000000001006608, "min": 1.0, "max": 3.0, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline arrivals as demand proxy for forecasting
    # Pipeline orders represent past demands that triggered those orders
    if len(pipeline_orders) >= demand_forecast_window:
        recent_demands = pipeline_orders[:demand_forecast_window]
    else:
        recent_demands = pipeline_orders if pipeline_orders else [0]

    # Calculate forecast with simple moving average
    demand_forecast = sum(recent_demands) / len(recent_demands)

    # Adjust base stock dynamically based on demand variability
    if recent_demands:
        max_demand = max(recent_demands)
        min_demand = min(recent_demands)
        demand_variability = max_demand - min_demand
        adjusted_base_stock = base_stock + safety_multiplier * demand_variability
    else:
        adjusted_base_stock = base_stock

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock + demand_forecast

    # Calculate order needed to reach target
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing to avoid extreme fluctuations
    smoothed_order = order_smoothing * max(0, order_needed) + (1 - order_smoothing) * demand_forecast

    # Round to integer and ensure non-negative
    order_amount = int(round(smoothed_order))
    order_amount = max(0, order_amount)

    return order_amount
