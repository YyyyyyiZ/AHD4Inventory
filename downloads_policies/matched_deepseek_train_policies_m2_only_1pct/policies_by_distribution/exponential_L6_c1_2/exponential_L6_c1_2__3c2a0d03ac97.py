# policy_hash: 3c2a0d03ac9749a2585ee2a321cda68e277f67ee30eb5fa680407ddd365e6537
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 7200.12
# best_prompt_performance: 7200.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_034509.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 351.93549911785453  # OPT_PARAM: {"initial": 351.93549911785453, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 44.97534167522155  # OPT_PARAM: {"initial": 44.97534167522155, "min": 0, "max": 200, "type": "float"}
    pipeline_coverage = 1.152729082511478  # OPT_PARAM: {"initial": 1.152729082511478, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate pipeline-adjusted base stock
    pipeline_sum = sum(pipeline_orders)
    adjusted_base = base_stock + safety_stock - pipeline_coverage * pipeline_sum

    # Ensure non-negative order
    order_amount = max(0, adjusted_base - on_hand_inventory)

    return order_amount
