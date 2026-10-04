# policy_hash: fa59558b440ba7b1f58b9e88ba3f39d73183e3db7fad78306598697c72692a8f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 6123.56
# best_prompt_performance: 6123.68
# best_rel_error_pct: 0.001960
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001441.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 289.1473562047933  # OPT_PARAM: {"initial": 289.1473562047933, "min": 200, "max": 400, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.18637667879029732  # OPT_PARAM: {"initial": 0.18637667879029732, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.23617283413705198  # OPT_PARAM: {"initial": 0.23617283413705198, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.4, "type": "float"}
    lost_sales_weight = 2.3870857709980626  # OPT_PARAM: {"initial": 2.3870857709980626, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Dynamic safety stock based on recent pipeline variability
    if len(pipeline_orders) >= 2:
        recent_values = [p for p in pipeline_orders[:3] if p > 0]
        if recent_values:
            avg_recent = sum(recent_values) / len(recent_values)
            safety_stock = safety_stock_factor * avg_recent
        else:
            safety_stock = 0
    else:
        safety_stock = 0

    # Adjust base stock based on cost ratio (favor holding over lost sales)
    adjusted_base_stock = base_stock * lost_sales_weight / (1 + lost_sales_weight)

    # Target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Base order calculation
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing using recent orders
    if pipeline_orders:
        # Use weighted average of recent pipeline orders
        recent_weights = [0.6, 0.3, 0.1][:len(pipeline_orders)]
        recent_avg = sum(w * p for w, p in zip(recent_weights, pipeline_orders))
        order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * recent_avg
    else:
        order_amount = base_order

    # Add demand-responsive adjustment based on trend
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0 and pipeline_orders[1] > 0:
        trend = pipeline_orders[0] - pipeline_orders[1]
        adjustment = demand_forecast_factor * trend
        order_amount = max(0, order_amount + adjustment)

    # Ensure order amount is integer
    order_amount = int(round(order_amount))

    return order_amount
