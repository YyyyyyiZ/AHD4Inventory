# policy_hash: ecfd2b3d3a56e0a32414c0d5d69a3525098c352ef9b488a51a82ff3e79daaa5d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 1727.92
# best_prompt_performance: 1727.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_183528.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 481.979022078215  # OPT_PARAM: {"initial": 481.979022078215, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
