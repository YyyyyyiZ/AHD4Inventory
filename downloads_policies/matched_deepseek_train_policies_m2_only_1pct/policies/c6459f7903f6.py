# policy_hash: c6459f7903f63f0fd2cb07e45a41b9c997da44c8fb27639a96b8f32c9e73d22b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 7212.78
# best_prompt_performance: 7210.63
# best_rel_error_pct: 0.029808
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052202.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 357.6569083662844  # OPT_PARAM: {"initial": 357.6569083662844, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.69675092365272  # OPT_PARAM: {"initial": 50.69675092365272, "min": 0, "max": 200, "type": "float"}
    pipeline_ratio = 0.14029367562171285  # OPT_PARAM: {"initial": 0.14029367562171285, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    pipeline_sum = sum(pipeline_orders)
    adjusted_base = base_stock + safety_stock - pipeline_ratio * pipeline_sum

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    return order_amount
