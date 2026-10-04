# policy_hash: 687d24d04a8b3e4023ed90879c9f5f1b540302451af454219376448f7cb5ad00
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 151
# source_prompt_files: 1
# best_target_performance: 6033.8
# best_prompt_performance: 6033.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_062554.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 692.0049957614882  # OPT_PARAM: {"initial": 692.0049957614882, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
