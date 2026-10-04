# policy_hash: 8c0468db54a2bb72e9623d2e0c9e5894b19b1bac2a85d6c6e0e26862a04d941f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 10393.92
# best_prompt_performance: 10393.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032606.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 277.4571949315071  # OPT_PARAM: {"initial": 277.4571949315071, "min": 200, "max": 450, "type": "float"}
    safety_stock = 27.75040737544526  # OPT_PARAM: {"initial": 27.75040737544526, "min": 25, "max": 80, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing = 0.31562432441664234  # OPT_PARAM: {"initial": 0.31562432441664234, "min": 0.3, "max": 0.9, "type": "float"}
    demand_anticipation = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline with stronger emphasis on near-term arrivals
    weighted_pipeline = 0
    total_weight = 0
    for i, qty in enumerate(pipeline_orders):
        # Exponential decay weight: more weight to immediate arrivals
        weight = 0.7000000000000155  # OPT_PARAM: {"initial": 0.7000000000000155, "min": 0.5, "max": 0.9, "type": "float"}
        weighted_pipeline += qty * weight
        total_weight += weight

    # Normalize weighted pipeline
    if total_weight > 0:
        normalized_pipeline = weighted_pipeline / total_weight
    else:
        normalized_pipeline = 0

    # Adjust target based on pipeline coverage
    if sum(pipeline_orders) > 0:
        coverage_ratio = normalized_pipeline / (sum(pipeline_orders) / len(pipeline_orders))
        coverage_ratio = min(max(coverage_ratio, 0.5), 1.5)  # Bound the ratio
    else:
        coverage_ratio = 1.0

    # Dynamic target calculation
    pipeline_adjustment = 1.0 - pipeline_weight * (1.0 - coverage_ratio)
    target_inventory = (base_stock * pipeline_adjustment) + safety_stock

    # Add demand anticipation based on recent pipeline activity
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        anticipation = demand_anticipation * recent_avg
        target_inventory += anticipation

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with adaptive factor
    if pipeline_orders:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        recent_avg = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to integer
    return order_amount
