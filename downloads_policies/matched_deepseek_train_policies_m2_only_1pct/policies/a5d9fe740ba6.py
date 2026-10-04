# policy_hash: a5d9fe740ba6cf9a2863c4d2a094c6a6bf23da773e740d8964bddade908fb42d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6824.57
# best_prompt_performance: 6824.57
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091603.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 331.95095612827777  # OPT_PARAM: {"initial": 331.95095612827777, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.99079868564055  # OPT_PARAM: {"initial": 24.99079868564055, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    return order_amount
