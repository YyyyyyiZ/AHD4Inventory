# policy_hash: d1438f0a6e6c99457f26434efe524513ded43b17cdfd16abea6af6863b282291
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 6107.84
# best_prompt_performance: 6107.82
# best_rel_error_pct: 0.000327
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000932.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 244.36718899081154  # OPT_PARAM: {"initial": 244.36718899081154, "min": 150, "max": 400, "type": "float"}
    safety_stock = 5.7814053405770505  # OPT_PARAM: {"initial": 5.7814053405770505, "min": 0, "max": 50, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1557565350926912  # OPT_PARAM: {"initial": 0.1557565350926912, "min": 0.1, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - effective_inventory)

    # Apply smoothing using weighted average of recent orders
    if pipeline_orders:
        # Give more weight to recent orders
        weights = [0.5, 0.3, 0.15, 0.05][:len(pipeline_orders)]
        weights = [w/sum(weights) for w in weights]
        weighted_avg = sum(w * o for w, o in zip(weights, pipeline_orders))
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * weighted_avg

    # Add demand-responsive adjustment
    if pipeline_orders and len(pipeline_orders) >= 2:
        recent_trend = pipeline_orders[0] - pipeline_orders[1]
        adjustment = demand_forecast_factor * recent_trend
        order_amount = max(0, order_amount + adjustment)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
