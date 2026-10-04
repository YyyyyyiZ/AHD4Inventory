# policy_hash: 262e71cb82f4b70ee50eac0313287f6f8ff20779809e3f6a94635ce5f5de12a9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 98
# source_prompt_files: 1
# best_target_performance: 1392.5
# best_prompt_performance: 1392.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_234628.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.00031799336546  # OPT_PARAM: {"initial": 308.00031799336546, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
