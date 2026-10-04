# policy_hash: 0697f911d36e82e62e58d41badf5f830834e90d320684134a91836631e46dbd2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 73
# source_prompt_files: 1
# best_target_performance: 8590.22
# best_prompt_performance: 8590.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_085614.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 687.9098938403151  # OPT_PARAM: {"initial": 687.9098938403151, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
