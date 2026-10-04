# policy_hash: eaecb26f62f0e2cbc61cf2ca768401ef7e42e65198e4c3fe2b4da6a1c9e9ad58
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 93
# source_prompt_files: 1
# best_target_performance: 13069.62
# best_prompt_performance: 13069.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015312.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 553.9875397341209  # OPT_PARAM: {"initial": 553.9875397341209, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
