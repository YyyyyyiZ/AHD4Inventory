# policy_hash: 1c9f5795c3cff01a25dad8b8185780a8d50032d1c590c0a5d971bf059d38a5d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 9
# source_prompt_files: 2
# best_target_performance: 11778.73
# best_prompt_performance: 11778.7
# best_rel_error_pct: 0.000255
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020634.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 369.77025000981274  # OPT_PARAM: {"initial": 369.77025000981274, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 81.08421208235478  # OPT_PARAM: {"initial": 81.08421208235478, "min": 80, "max": 200, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    min_order = 25.55869093775709  # OPT_PARAM: {"initial": 25.55869093775709, "min": 0, "max": 50, "type": "float"}
    max_order = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 200, "max": 600, "type": "float"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = total_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Estimate expected demand from recent pipeline arrivals
    if len(pipeline_orders) >= 4:
        # Use more recent orders for better demand estimation
        recent_orders = pipeline_orders[1:4]
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
        expected_demand = avg_recent_demand * demand_buffer
    else:
        expected_demand = 0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + expected_demand

    # Base-stock policy calculation
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with recent order patterns
    if len(pipeline_orders) >= 2:
        avg_recent = sum(pipeline_orders[-2:]) / 2
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
