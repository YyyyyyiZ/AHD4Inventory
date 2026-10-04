# policy_hash: aa72dba0d063f930e59d524c976f324d6730290d560688dbdd6bd08f0e5f73cf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 5539.36
# best_prompt_performance: 5539.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_172406.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 533.9521701419602  # OPT_PARAM: {"initial": 533.9521701419602, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
