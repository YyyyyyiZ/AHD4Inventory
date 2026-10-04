# policy_hash: 721b0efe68f1b24e11969a2c3e804c2bedbb08737f1a8c296fe79bce5a218cea
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 3336.88
# best_prompt_performance: 3336.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053124.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 697.9997255235969  # OPT_PARAM: {"initial": 697.9997255235969, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
