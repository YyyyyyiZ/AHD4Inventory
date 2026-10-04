# policy_hash: 69c96ddb22e186a607bae87e7ce74f9f33d8a327c6fe36985089d1029abb02ee
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 43
# source_prompt_files: 2
# best_target_performance: 6950.32
# best_prompt_performance: 6950.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034559.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.9634550836068  # OPT_PARAM: {"initial": 282.9634550836068, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
