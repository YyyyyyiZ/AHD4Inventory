# policy_hash: fc003338f721b577da82d2a134d8b992e37ccda7921c9023ac6ed03bde5d4f33
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 52
# source_prompt_files: 1
# best_target_performance: 12085.92
# best_prompt_performance: 12085.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083521.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 448.99993377977387  # OPT_PARAM: {"initial": 448.99993377977387, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
