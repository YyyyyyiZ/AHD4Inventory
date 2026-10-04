# policy_hash: e28346cad92f54c0f9aad261f1dc9eec03dead09d8aa609c4eefb90416c45b37
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 103
# source_prompt_files: 1
# best_target_performance: 1031.2
# best_prompt_performance: 1031.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_021407.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
