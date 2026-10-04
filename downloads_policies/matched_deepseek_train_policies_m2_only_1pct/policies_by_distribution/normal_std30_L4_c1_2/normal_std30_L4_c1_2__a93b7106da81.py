# policy_hash: a93b7106da813660028c252f81c4931f20156f8b37bc243a420d3381254c1c2b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_2
# matched_train_cells: 103
# source_prompt_files: 1
# best_target_performance: 3214.44
# best_prompt_performance: 3214.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_073622.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 437.0000345179279  # OPT_PARAM: {"initial": 437.0000345179279, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
