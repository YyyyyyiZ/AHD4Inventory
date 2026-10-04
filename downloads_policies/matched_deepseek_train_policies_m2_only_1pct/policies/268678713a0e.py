# policy_hash: 268678713a0ec0c61dc2279e0e23387ff7d0159752a918a14e5dcbeb8d494406
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 60
# source_prompt_files: 1
# best_target_performance: 1772.1
# best_prompt_performance: 1772.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_074256.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 482.9217190211206  # OPT_PARAM: {"initial": 482.9217190211206, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
