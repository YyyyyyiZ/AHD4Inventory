# policy_hash: d057e293ba626171c18f40196cf90cdb3689d54e56189fa5bf1771d9c8ace2a6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1237.56
# best_prompt_performance: 1237.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072732.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 344.20049847806513  # OPT_PARAM: {"initial": 344.20049847806513, "min": 200, "max": 400, "type": "float"}
    safety_stock = 64.20049847807137  # OPT_PARAM: {"initial": 64.20049847807137, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.8, "max": 1.3, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    order_smoothing = 0.6698119155568046  # OPT_PARAM: {"initial": 0.6698119155568046, "min": 0.0, "max": 0.8, "type": "float"}
    demand_floor = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 70, "max": 110, "type": "float"}
    demand_cap = 130.0  # OPT_PARAM: {"initial": 130.0, "min": 110, "max": 150, "type": "float"}
    pipeline_lookback = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 5, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    # Use more lookback periods for better stability
    if len(pipeline_orders) >= pipeline_lookback:
        recent_orders = pipeline_orders[-pipeline_lookback:]
        # Exponential weighting: most recent gets highest weight
        weights = [0.5 ** (pipeline_lookback - i) for i in range(1, pipeline_lookback + 1)]
        weighted_avg = sum(w * o for w, o in zip(weights, recent_orders)) / sum(weights)
        demand_estimate = weighted_avg * demand_adjustment
        # Apply bounds to prevent extreme estimates
        demand_estimate = max(demand_floor, min(demand_cap, demand_estimate))
    else:
        demand_estimate = 100.0  # Default estimate

    # Calculate target inventory level with dynamic safety stock
    # Safety stock increases with demand estimate
    adjusted_safety = safety_stock * (demand_estimate / 100.0)
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
