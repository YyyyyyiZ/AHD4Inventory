# policy_hash: 03e95f69af1b94638b25af53ee544c600c9affc24b24d9ff2399c077f75062f5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 55
# source_prompt_files: 1
# best_target_performance: 4193.86
# best_prompt_performance: 4193.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_014235.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 594.9189518067652  # OPT_PARAM: {"initial": 594.9189518067652, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
