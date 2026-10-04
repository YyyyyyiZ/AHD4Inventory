# policy_hash: b4d3a81e9ff7e773b900640ec8d935c61a635149bb55311e16993eeec458deb9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 74
# source_prompt_files: 1
# best_target_performance: 3403.36
# best_prompt_performance: 3403.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_001739.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 693.000272399625  # OPT_PARAM: {"initial": 693.000272399625, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
