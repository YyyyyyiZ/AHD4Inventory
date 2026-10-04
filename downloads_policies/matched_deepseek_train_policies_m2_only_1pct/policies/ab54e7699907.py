# policy_hash: ab54e7699907828bb2add1250e25d6fba71c6337c33444e3b18fc361db75c1bf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 6193.86
# best_prompt_performance: 6193.82
# best_rel_error_pct: 0.000646
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075747.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 260.7841713856265  # OPT_PARAM: {"initial": 260.7841713856265, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 27.82071630201496  # OPT_PARAM: {"initial": 27.82071630201496, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.10013598391379563  # OPT_PARAM: {"initial": 0.10013598391379563, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock adjustment
    target_inventory = base_stock + safety_stock

    # Calculate order amount with demand forecasting consideration
    # Use a simple forecast based on recent pipeline orders
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Last two orders placed
        avg_recent_order = sum(recent_orders) / len(recent_orders)
        forecast_adjustment = avg_recent_order * demand_forecast_factor
    else:
        forecast_adjustment = 0

    # Adjust target based on forecast
    adjusted_target = target_inventory + forecast_adjustment

    # Calculate order amount
    order_amount = max(0, adjusted_target - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
