# policy_hash: a6334ff6adcd512b6263ac814d50d23dbf7ff5a9803dbe727e4fd0966497feaf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 11917.56
# best_prompt_performance: 11917.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031200.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.93124999998804  # OPT_PARAM: {"initial": 324.93124999998804, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = [pipeline_orders[0]] if pipeline_orders else [0]
    if len(pipeline_orders) > 1:
        recent_arrivals.append(pipeline_orders[1])

    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    forecast_demand = avg_recent_demand * demand_forecast_factor

    # Adjust base stock based on forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    max_order_adjustment = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 10, "max": 300, "type": "float"}
    if order_amount > max_order_adjustment:
        order_amount = max_order_adjustment + (order_amount - max_order_adjustment) * 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.9, "type": "float"}

    return order_amount
