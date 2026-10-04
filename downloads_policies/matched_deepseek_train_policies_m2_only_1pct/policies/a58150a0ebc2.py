# policy_hash: a58150a0ebc2cecbfc13217f40d815f28e2304fc8580ac124b6779b7f5875b7a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 1243.1
# best_prompt_performance: 1243.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072527.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 309.998004602503  # OPT_PARAM: {"initial": 309.998004602503, "min": 280, "max": 340, "type": "float"}
    safety_stock = 43.145469736823344  # OPT_PARAM: {"initial": 43.145469736823344, "min": 30, "max": 60, "type": "float"}
    demand_adjustment = 1.02  # OPT_PARAM: {"initial": 1.02, "min": 0.95, "max": 1.15, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    order_smoothing = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.7, "type": "float"}
    lost_sales_weight = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 1.5, "type": "float"}
    cost_ratio_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    if len(pipeline_orders) >= 2:
        weights = [pipeline_weight, 1.0 - pipeline_weight]
        recent_orders = pipeline_orders[-2:]
        weighted_avg = sum(w * o for w, o in zip(weights, recent_orders)) / sum(weights)
        demand_estimate = weighted_avg * demand_adjustment
    else:
        demand_estimate = 100.0

    # Adjust safety stock based on cost ratio with more conservative factor
    adjusted_safety = safety_stock * lost_sales_weight * cost_ratio_factor

    # Calculate target inventory level
    target_inventory = base_stock + adjusted_safety - demand_estimate

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * last_order + (1 - order_smoothing) * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
