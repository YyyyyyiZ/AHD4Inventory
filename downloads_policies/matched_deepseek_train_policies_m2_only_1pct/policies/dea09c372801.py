# policy_hash: dea09c3728013bf3523fd9d93d72ee957f8d3a05083ef172e9b26ab8502ec2d2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6072.12
# best_prompt_performance: 6091.98
# best_rel_error_pct: 0.327069
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000356.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 314.5719139121662  # OPT_PARAM: {"initial": 314.5719139121662, "min": 200, "max": 500, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1478604385948324  # OPT_PARAM: {"initial": 0.1478604385948324, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.28999443783433476  # OPT_PARAM: {"initial": 0.28999443783433476, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Dynamic safety stock based on recent demand variability
    if len(pipeline_orders) >= 2:
        recent_demand_est = pipeline_orders[0] if pipeline_orders[0] > 0 else pipeline_orders[1]
        safety_stock = safety_stock_factor * recent_demand_est
    else:
        safety_stock = 0

    # Target inventory position
    target_inventory = base_stock + safety_stock

    # Base order calculation
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing using recent orders
    if pipeline_orders:
        # Simple exponential smoothing of recent orders
        recent_avg = sum(pipeline_orders[:2]) / min(2, len(pipeline_orders))
        order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * recent_avg
    else:
        order_amount = base_order

    # Add demand-responsive adjustment based on trend
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0 and pipeline_orders[1] > 0:
        trend = pipeline_orders[0] - pipeline_orders[1]
        adjustment = demand_forecast_factor * trend
        order_amount = max(0, order_amount + adjustment)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
