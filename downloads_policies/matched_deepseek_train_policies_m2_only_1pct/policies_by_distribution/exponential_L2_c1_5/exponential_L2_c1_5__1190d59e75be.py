# policy_hash: 1190d59e75be1216311367b0e8ab2278dcfacc036acd5282d2da350f3d6b2932
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 10388.28
# best_prompt_performance: 10388.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032457.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.47084217798766  # OPT_PARAM: {"initial": 284.47084217798766, "min": 250, "max": 400, "type": "float"}
    safety_stock = 22.785740080194074  # OPT_PARAM: {"initial": 22.785740080194074, "min": 20, "max": 60, "type": "float"}
    pipeline_weight = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.4, "max": 0.9, "type": "float"}
    smoothing = 0.3402284355484524  # OPT_PARAM: {"initial": 0.3402284355484524, "min": 0.1, "max": 0.5, "type": "float"}
    demand_anticipation = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.6, "type": "float"}
    immediate_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.6, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline with emphasis on immediate arrivals
    weighted_pipeline = 0
    total_weight = 0
    for i, qty in enumerate(pipeline_orders):
        # Higher weight for immediate arrivals (exponential decay)
        weight = immediate_weight ** i
        weighted_pipeline += qty * weight
        total_weight += weight

    # Normalize weighted pipeline
    if total_weight > 0:
        normalized_pipeline = weighted_pipeline / total_weight
    else:
        normalized_pipeline = 0

    # Simple pipeline coverage adjustment
    if sum(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if avg_pipeline > 0:
            coverage_ratio = normalized_pipeline / avg_pipeline
            coverage_ratio = min(max(coverage_ratio, 0.6), 1.4)
        else:
            coverage_ratio = 1.0
    else:
        coverage_ratio = 1.0

    # Dynamic target calculation
    pipeline_adjustment = 1.0 - pipeline_weight * (1.0 - coverage_ratio)
    target_inventory = (base_stock * pipeline_adjustment) + safety_stock

    # Add demand anticipation based on recent pipeline
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        anticipation = demand_anticipation * recent_avg
        target_inventory += anticipation

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if pipeline_orders:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        recent_avg = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to integer
    return order_amount
