# policy_hash: f3b0209ea380d8a4a1ccda6dec1647acd4951e206c1199eb6428a1f1cee5d50b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 5237.13
# best_prompt_performance: 5268.58
# best_rel_error_pct: 0.600520
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_233858.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 404.0856686440938  # OPT_PARAM: {"initial": 404.0856686440938, "min": 100, "max": 800, "type": "float"}
    safety_stock = 6.182649919774005  # OPT_PARAM: {"initial": 6.182649919774005, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.2342363960699069  # OPT_PARAM: {"initial": 0.2342363960699069, "min": 0.1, "max": 2.0, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 12, "type": "int"}
    smoothing_factor = 0.2863819055752936  # OPT_PARAM: {"initial": 0.2863819055752936, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand using exponential smoothing of pipeline orders
    if len(pipeline_orders) > 0:
        # Use recent pipeline orders as proxy for demand
        recent_orders = pipeline_orders[:min(3, len(pipeline_orders))]
        recent_avg = sum(recent_orders) / len(recent_orders)

        # Apply exponential smoothing
        if 'last_forecast' not in compute_order_amount.__dict__:
            compute_order_amount.last_forecast = recent_avg
        forecast = smoothing_factor * recent_avg + (1 - smoothing_factor) * compute_order_amount.last_forecast
        compute_order_amount.last_forecast = forecast

        expected_demand = forecast * demand_forecast_factor
    else:
        expected_demand = 0

    # Adjust base stock for lead time demand
    lead_time_demand = expected_demand * lead_time

    # Calculate target inventory position
    target_inventory = base_stock + lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
