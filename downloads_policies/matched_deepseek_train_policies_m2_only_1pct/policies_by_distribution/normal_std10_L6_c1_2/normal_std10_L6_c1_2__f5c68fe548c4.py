# policy_hash: f5c68fe548c4571c59ebfc651b33a4c5b700bc85ac37559a178278833b26285d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 2753.6
# best_prompt_performance: 2753.6
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_034752.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 664.9760660333361  # OPT_PARAM: {"initial": 664.9760660333361, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
