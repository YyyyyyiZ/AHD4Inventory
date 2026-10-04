# policy_hash: 258d98e00edb270559454d09c758a8eb3f12a07c8ed311bbbf0120b31d9f3c9e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 10211.99
# best_prompt_performance: 10211.99
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034211.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 344.1071487351679  # OPT_PARAM: {"initial": 344.1071487351679, "min": 250, "max": 400, "type": "float"}
    safety_stock = 39.107148735172224  # OPT_PARAM: {"initial": 39.107148735172224, "min": 10, "max": 40, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.4, "max": 0.9, "type": "float"}
    smoothing = 0.36558317592725187  # OPT_PARAM: {"initial": 0.36558317592725187, "min": 0.2, "max": 0.6, "type": "float"}
    demand_anticipation = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.4, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average with more weight on near arrivals)
    if pipeline_orders:
        # Simple weighted average: more weight to orders arriving soon
        weights = [0.6, 0.4] if len(pipeline_orders) == 2 else [1.0]
        weighted_sum = sum(q * w for q, w in zip(pipeline_orders, weights))
        effective_pipeline = weighted_sum / sum(weights[:len(pipeline_orders)])
    else:
        effective_pipeline = 0

    # Calculate pipeline adjustment factor
    if effective_pipeline > 0:
        # Normalize by base_stock to get pipeline coverage ratio
        pipeline_ratio = effective_pipeline / base_stock
        # Adjust target based on pipeline: more pipeline → lower target
        pipeline_adjustment = 1.0 - pipeline_weight * min(pipeline_ratio, 1.0)
    else:
        pipeline_adjustment = 1.0

    # Target inventory calculation
    target_inventory = base_stock * pipeline_adjustment + safety_stock

    # Add demand anticipation based on recent pipeline (proxy for recent demand)
    if len(pipeline_orders) >= 2:
        recent_pipeline = sum(pipeline_orders[-2:]) / 2
        target_inventory += demand_anticipation * recent_pipeline

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with recent order history
    if pipeline_orders:
        recent_order = pipeline_orders[-1] if pipeline_orders else 0
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    return order_amount
