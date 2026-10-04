# policy_hash: 930818861f3e9a8cd4be091a19325f06df18c23932be6f0b4ee6a617d8f35be0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 44
# source_prompt_files: 1
# best_target_performance: 11228.03
# best_prompt_performance: 11227.8
# best_rel_error_pct: 0.002048
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005816.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 309.46831711684695  # OPT_PARAM: {"initial": 309.46831711684695, "min": 200, "max": 450, "type": "float"}
    safety_factor = 1.6034498595241  # OPT_PARAM: {"initial": 1.6034498595241, "min": 0.5, "max": 2.0, "type": "float"}
    smoothing = 0.14764490265759458  # OPT_PARAM: {"initial": 0.14764490265759458, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight = 0.1567580317880029  # OPT_PARAM: {"initial": 0.1567580317880029, "min": 0.0, "max": 1.0, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of pipeline orders
    if pipeline_orders:
        # Give more weight to recent orders
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]
        weighted_avg = sum(p * w for p, w in zip(pipeline_orders, weights))
        demand_estimate = weighted_avg * safety_factor
    else:
        demand_estimate = base_stock * 0.25

    # Dynamic target: base stock plus safety stock based on demand estimate
    target_inventory = base_stock + demand_estimate

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with consideration of pipeline orders
    if pipeline_orders:
        # Use average of recent pipeline orders as reference
        recent_avg = sum(pipeline_orders[-2:]) / min(2, len(pipeline_orders))
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
    else:
        smoothed_order = raw_order

    # Apply minimum order constraint
    if smoothed_order < min_order:
        smoothed_order = min_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
