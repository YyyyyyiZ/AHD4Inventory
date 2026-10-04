# policy_hash: a4560eabd57e1d16a77a823c3e357ac820f131a8d0e1bd287583ed5b87ad0ca3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 35
# source_prompt_files: 1
# best_target_performance: 2497.62
# best_prompt_performance: 2497.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_020029.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 638.2571288677915  # OPT_PARAM: {"initial": 638.2571288677915, "min": 400, "max": 900, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_forecast_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.5, "max": 2.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline contribution for demand forecasting
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_pipeline = sum(w * q for w, q in zip(weights, pipeline_orders))
        total_weight = sum(weights)
        avg_weighted_demand = weighted_pipeline / total_weight
    else:
        avg_weighted_demand = 100.0

    # Adjust base stock based on demand forecast
    demand_adjustment = demand_forecast_factor * (avg_weighted_demand - 100)
    adjusted_base_stock = base_stock + demand_adjustment

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing using recent pipeline orders
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(2, len(pipeline_orders)):]
        avg_recent = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
