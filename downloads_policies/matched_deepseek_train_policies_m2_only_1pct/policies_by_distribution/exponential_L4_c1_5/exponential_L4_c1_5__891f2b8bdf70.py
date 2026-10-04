# policy_hash: 891f2b8bdf70ade1781e3a60864cc9d3067755207892a74fe8f453b5f53a900b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 11382.02
# best_prompt_performance: 11382.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003532.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 361.40000000003465  # OPT_PARAM: {"initial": 361.40000000003465, "min": 200, "max": 500, "type": "float"}
    safety_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders
    if pipeline_orders:
        # Use average of recent orders as demand estimate
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        demand_estimate = avg_pipeline * safety_factor
    else:
        demand_estimate = base_stock * 0.3

    # Dynamic target based on demand estimate
    target_inventory = base_stock + demand_estimate

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    if pipeline_orders:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
