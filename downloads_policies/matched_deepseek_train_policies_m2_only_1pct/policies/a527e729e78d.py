# policy_hash: a527e729e78d8a526e45d80110562bb78ad72880f7c8778cdcd90abdf7a3ab67
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 135
# source_prompt_files: 1
# best_target_performance: 4699.28
# best_prompt_performance: 4699.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_043628.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 506.9564661655399  # OPT_PARAM: {"initial": 506.9564661655399, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
