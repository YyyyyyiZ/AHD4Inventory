# policy_hash: a899b705f6fc1e4a5c9375ea3cd6ec1ec5c439c4920c2e4a0beae2161450ce84
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 181
# source_prompt_files: 1
# best_target_performance: 1021.36
# best_prompt_performance: 1021.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_200703.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 296.00009215267653  # OPT_PARAM: {"initial": 296.00009215267653, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
