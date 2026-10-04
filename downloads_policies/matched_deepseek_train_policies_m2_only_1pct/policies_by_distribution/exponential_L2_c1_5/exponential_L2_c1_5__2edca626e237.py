# policy_hash: 2edca626e237784241663924f520da1d2a1520a06729f3bc3dd59ceda6e1b3b8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 10796.2
# best_prompt_performance: 10796.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030945.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.93124999998804  # OPT_PARAM: {"initial": 324.93124999998804, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
