# policy_hash: a5f4596a5691e3010a313c4b8b698cdecc555a79738fb36fc0b8466370406afb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 2
# best_target_performance: 6184.3
# best_prompt_performance: 6184.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075957.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 271.62324772784956  # OPT_PARAM: {"initial": 271.62324772784956, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.5988971077718288  # OPT_PARAM: {"initial": 0.5988971077718288, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]  # Oldest arriving orders
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals) * demand_forecast_factor
    else:
        demand_estimate = 0

    # Adjust base stock based on demand estimate
    adjusted_base_stock = base_stock + demand_estimate

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
