# policy_hash: c9cdf91846bb695dffb1324b245d46854c7e7f22fed518917a2f03fc492acec8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 1254.58
# best_prompt_performance: 1254.58
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072046.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 327.79175997593757  # OPT_PARAM: {"initial": 327.79175997593757, "min": 250, "max": 380, "type": "float"}
    safety_stock = 43.73417480227656  # OPT_PARAM: {"initial": 43.73417480227656, "min": 20, "max": 80, "type": "float"}
    demand_adjustment = 1.02  # OPT_PARAM: {"initial": 1.02, "min": 0.9, "max": 1.15, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.6, "max": 1.0, "type": "float"}
    order_smoothing = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.7, "type": "float"}
    lost_sales_weight = 1.7883573295611954  # OPT_PARAM: {"initial": 1.7883573295611954, "min": 1.2, "max": 2.5, "type": "float"}

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

    # Adjust target based on cost ratio (p=5, h=1)
    # Higher weight on avoiding lost sales
    cost_adjusted_target = base_stock + safety_stock * lost_sales_weight - demand_estimate

    # Calculate raw order amount
    raw_order = max(0, cost_adjusted_target - inventory_position)

    # Apply smoothing to reduce order volatility
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * last_order + (1 - order_smoothing) * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
