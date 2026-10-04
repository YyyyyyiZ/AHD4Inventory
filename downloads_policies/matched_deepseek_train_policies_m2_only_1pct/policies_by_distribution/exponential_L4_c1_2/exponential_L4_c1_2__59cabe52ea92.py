# policy_hash: 59cabe52ea92e55a829ec3117865aba2b6e27191000bd9266edc5e95692145a0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6131.6
# best_prompt_performance: 6132.7
# best_rel_error_pct: 0.017940
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000844.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 342.38045903105353  # OPT_PARAM: {"initial": 342.38045903105353, "min": 250, "max": 450, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.13364034468144848  # OPT_PARAM: {"initial": 0.13364034468144848, "min": 0.1, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.09380172926617654  # OPT_PARAM: {"initial": 0.09380172926617654, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Dynamic safety stock based on recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        recent_arrivals = [p for p in pipeline_orders[:2] if p > 0]
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
        recent_weights = [0.6, 0.4] if len(pipeline_orders) >= 2 else [1.0]
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
