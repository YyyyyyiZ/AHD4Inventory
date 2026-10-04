# policy_hash: 6331fbad0c96b3f8bd8f2e48ded7273a488187678cf4a622d857b4bea77e731e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 1047.97
# best_prompt_performance: 1047.97
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_043933.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 471.4983994669374  # OPT_PARAM: {"initial": 471.4983994669374, "min": 300, "max": 700, "type": "float"}
    safety_stock = 13.50830456087962  # OPT_PARAM: {"initial": 13.50830456087962, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.057446582799631  # OPT_PARAM: {"initial": 0.057446582799631, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base stock policy with smoothing
    raw_order = max(0, base_stock + safety_stock - inventory_position)

    # Apply smoothing using last order if available
    if pipeline_orders:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1]
    else:
        order_amount = raw_order

    return order_amount
