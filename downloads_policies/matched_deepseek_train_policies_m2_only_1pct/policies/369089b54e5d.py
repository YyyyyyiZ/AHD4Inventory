# policy_hash: 369089b54e5d5e191c448c32be23ccd842741b790ea1456537068617d6ae3623
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 38
# source_prompt_files: 1
# best_target_performance: 7242.44
# best_prompt_performance: 7242.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_033832.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.9601574426319  # OPT_PARAM: {"initial": 356.9601574426319, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
