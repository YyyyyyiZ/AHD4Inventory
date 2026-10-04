# policy_hash: 663c57bbfcf5ebd4d6587644204dac0e4d5589d4a47caa092b675837713fce51
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5630.72
# best_prompt_performance: 5630.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_010949.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 533.9521701419602  # OPT_PARAM: {"initial": 533.9521701419602, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    pipeline_coef = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_coef
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
