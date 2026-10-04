# policy_hash: ded01449e67e01529dc01befbd0ca66fbb89765570b318dbd21484144ec6f351
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 46
# source_prompt_files: 1
# best_target_performance: 6301.87
# best_prompt_performance: 6301.87
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103649.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 207.94635405797283  # OPT_PARAM: {"initial": 207.94635405797283, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
