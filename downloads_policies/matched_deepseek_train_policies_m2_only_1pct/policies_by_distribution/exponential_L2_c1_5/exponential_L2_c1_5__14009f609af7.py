# policy_hash: 14009f609af76b88c749b19aaf9a972a9942e9b862d268377c232c5814fef4d1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 10360.0
# best_prompt_performance: 10360.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032726.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 278.47176492682433  # OPT_PARAM: {"initial": 278.47176492682433, "min": 150, "max": 400, "type": "float"}
    safety_stock = 38.471764926824015  # OPT_PARAM: {"initial": 38.471764926824015, "min": 20, "max": 100, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.9, "type": "float"}
    smoothing = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    # Give more weight to orders arriving sooner
    effective_pipeline = 0
    for i, qty in enumerate(pipeline_orders):
        weight = (len(pipeline_orders) - i) / len(pipeline_orders)
        effective_pipeline += qty * weight

    # Adjust target based on pipeline coverage
    if sum(pipeline_orders) > 0:
        coverage_ratio = effective_pipeline / sum(pipeline_orders)
    else:
        coverage_ratio = 1.0

    # Calculate target inventory level
    pipeline_adjustment = 1.0 - pipeline_weight * (1.0 - coverage_ratio)
    target_inventory = (base_stock * pipeline_adjustment) + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Smooth with recent pipeline activity
    if pipeline_orders:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        recent_avg = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to integer
    return order_amount
