# policy_hash: e8e42053455432977854265a6e566c3a5719b02c889de21e0a75c58f5688c3f3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 6238.52
# best_prompt_performance: 6238.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080058.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 271.14514518996845  # OPT_PARAM: {"initial": 271.14514518996845, "min": 100, "max": 500, "type": "float"}
    safety_stock = 10.720277394258162  # OPT_PARAM: {"initial": 10.720277394258162, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.0941623530555722  # OPT_PARAM: {"initial": 0.0941623530555722, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing_factor = 0.03531088239583959  # OPT_PARAM: {"initial": 0.03531088239583959, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline with more weight on near-term arrivals
    weighted_pipeline = 0
    total_weight = 0
    L = len(pipeline_orders)
    for i, q in enumerate(pipeline_orders):
        weight = (1 - pipeline_weight * i / L) if L > 0 else 1
        weighted_pipeline += q * weight
        total_weight += weight

    # Normalize weighted pipeline
    if total_weight > 0:
        weighted_pipeline = weighted_pipeline / total_weight * L

    # Calculate target inventory position
    target = base_stock + safety_stock - weighted_pipeline * pipeline_weight

    # Calculate raw order amount
    raw_order = max(0, target - inventory_position)

    # Apply exponential smoothing to order amounts
    # This helps reduce order volatility
    if 'prev_order' not in compute_order_amount.__dict__:
        compute_order_amount.prev_order = 0

    smoothed_order = (smoothing_factor * raw_order +
                     (1 - smoothing_factor) * compute_order_amount.prev_order)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))
    compute_order_amount.prev_order = order_amount

    return order_amount
