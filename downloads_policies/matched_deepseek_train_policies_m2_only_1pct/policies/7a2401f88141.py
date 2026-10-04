# policy_hash: 7a2401f881415be70b89394f1b9a65ebff4c65bc5ab21ba8bc4bc522466332ae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 73
# source_prompt_files: 1
# best_target_performance: 2183.78
# best_prompt_performance: 2183.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080853.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 502.9988103123368  # OPT_PARAM: {"initial": 502.9988103123368, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
