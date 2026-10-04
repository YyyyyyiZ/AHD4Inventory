# policy_hash: 47db25687a962678f786f6d675fd727cf537362a2d5a3773c3b94cd949673b81
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6168.2
# best_prompt_performance: 6168.12
# best_rel_error_pct: 0.001297
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082904.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.2456038980501  # OPT_PARAM: {"initial": 279.2456038980501, "min": 150, "max": 400, "type": "float"}
    safety_stock = 24.102563774074277  # OPT_PARAM: {"initial": 24.102563774074277, "min": 10, "max": 60, "type": "float"}
    pipeline_coverage = 0.7106520530573042  # OPT_PARAM: {"initial": 0.7106520530573042, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    demand_anticipation = 0.19841121984742277  # OPT_PARAM: {"initial": 0.19841121984742277, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage (discount future arrivals)
    effective_pipeline = pipeline_coverage * sum(pipeline_orders)

    # Adjust target based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (base_stock + 1e-6)
    pipeline_adjustment = 1.0 - demand_anticipation * min(1.0, pipeline_ratio)

    # Target inventory position with dynamic adjustment
    target_position = (base_stock + safety_stock) * pipeline_adjustment

    # Calculate order needed
    order_needed = target_position - (on_hand_inventory + effective_pipeline)

    # Apply smoothing to avoid extreme fluctuations
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * max(0, order_needed) + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = max(0, order_needed)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
