# policy_hash: d49f22d9185287066d51bd2fff654d31f2a63a9cae691a88256c1ef673174a6a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 17
# source_prompt_files: 2
# best_target_performance: 11094.6
# best_prompt_performance: 11094.6
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_043838.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 379.02879696200927  # OPT_PARAM: {"initial": 379.02879696200927, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 30.028863182215606  # OPT_PARAM: {"initial": 30.028863182215606, "min": 0, "max": 300, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 2 arriving orders as demand proxy
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    forecast_demand = sum(recent_arrivals) / max(len(recent_arrivals), 1) * demand_forecast_factor

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + forecast_demand + safety_stock

    # Calculate order amount with smoothing
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing to avoid extreme fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        # Smooth with previous order
        previous_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * previous_order

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
