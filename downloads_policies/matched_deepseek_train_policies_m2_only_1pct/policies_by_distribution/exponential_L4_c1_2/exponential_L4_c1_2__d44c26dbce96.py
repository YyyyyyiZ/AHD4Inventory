# policy_hash: d44c26dbce96ac4e5d75a8cdd218a88f17bbf5d442b0552798adae32293e1554
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 32
# source_prompt_files: 2
# best_target_performance: 6137.52
# best_prompt_performance: 6137.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001807.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.7565797622309  # OPT_PARAM: {"initial": 286.7565797622309, "min": 200, "max": 350, "type": "float"}
    pipeline_weight = 0.8209537358110576  # OPT_PARAM: {"initial": 0.8209537358110576, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.19391729712646089  # OPT_PARAM: {"initial": 0.19391729712646089, "min": 0.15, "max": 0.4, "type": "float"}
    demand_forecast_factor = 0.0807421079885226  # OPT_PARAM: {"initial": 0.0807421079885226, "min": 0.05, "max": 0.2, "type": "float"}
    safety_stock_factor = 0.09391729712646087  # OPT_PARAM: {"initial": 0.09391729712646087, "min": 0.05, "max": 0.25, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Dynamic safety stock based on recent pipeline arrivals
    if len(pipeline_orders) >= pipeline_lookback:
        recent_arrivals = [p for p in pipeline_orders[:pipeline_lookback] if p > 0]
        if recent_arrivals:
            avg_recent = sum(recent_arrivals) / len(recent_arrivals)
            safety_stock = safety_stock_factor * avg_recent
        else:
            safety_stock = 0
    else:
        safety_stock = 0

    # Target inventory position
    target_inventory = base_stock + safety_stock

    # Base order calculation
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing using recent orders
    if pipeline_orders:
        # Use weighted average of recent pipeline orders
        recent_weights = [0.7, 0.3] if len(pipeline_orders) >= 2 else [1.0]
        weighted_sum = 0
        total_weight = 0
        for i, weight in enumerate(recent_weights):
            if i < len(pipeline_orders):
                weighted_sum += weight * pipeline_orders[i]
                total_weight += weight
        recent_avg = weighted_sum / total_weight if total_weight > 0 else 0
        order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * recent_avg
    else:
        order_amount = base_order

    # Add demand-responsive adjustment based on trend
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0 and pipeline_orders[1] > 0:
        trend = pipeline_orders[0] - pipeline_orders[1]
        adjustment = demand_forecast_factor * trend
        order_amount = max(0, order_amount + adjustment)

    # Apply minimum order threshold to reduce small orders
    if order_amount < min_order_threshold:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
