# policy_hash: ea9e7140f9004d18b342d74439221f94341578188705091a0e6f4d115a67eddb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 10389.67
# best_prompt_performance: 10389.62
# best_rel_error_pct: 0.000481
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032757.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.43531848819686  # OPT_PARAM: {"initial": 286.43531848819686, "min": 200, "max": 500, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 80, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.9, "type": "float"}
    smoothing = 0.3299755111351586  # OPT_PARAM: {"initial": 0.3299755111351586, "min": 0.2, "max": 0.8, "type": "float"}
    demand_anticipation = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.6, "type": "float"}
    pipeline_decay = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.6, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline with decay
    weighted_pipeline = 0
    total_weight = 0
    for i, qty in enumerate(pipeline_orders):
        weight = pipeline_decay ** i
        weighted_pipeline += qty * weight
        total_weight += weight

    # Normalize weighted pipeline
    if total_weight > 0:
        normalized_pipeline = weighted_pipeline / total_weight
    else:
        normalized_pipeline = 0

    # Simple pipeline adjustment
    if sum(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_factor = normalized_pipeline / avg_pipeline if avg_pipeline > 0 else 1.0
        pipeline_factor = min(max(pipeline_factor, 0.7), 1.3)
    else:
        pipeline_factor = 1.0

    # Target inventory calculation
    target_inventory = base_stock * (1.0 - pipeline_weight * (1.0 - pipeline_factor)) + safety_stock

    # Add demand anticipation
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        target_inventory += demand_anticipation * recent_avg

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if pipeline_orders:
        recent_avg = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    return order_amount
