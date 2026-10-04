# policy_hash: 73d3d88875c86a0d825b8ec726cb292df8384f315f4a9d449ed47693eff01d30
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1453.86
# best_prompt_performance: 1444.68
# best_rel_error_pct: 0.631423
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_023506.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.3454724643828  # OPT_PARAM: {"initial": 420.3454724643828, "min": 300, "max": 600, "type": "float"}
    safety_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 2.5, "type": "float"}
    pipeline_coverage = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.33597450463447903  # OPT_PARAM: {"initial": 0.33597450463447903, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand coverage from pipeline
    pipeline_cover = pipeline_coverage * sum(pipeline_orders)

    # Target inventory position with dynamic adjustment
    target_position = base_stock + safety_factor * (base_stock - pipeline_cover)

    # Calculate raw order
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing to avoid large order swings
    smoothed_order = smoothing_factor * raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
