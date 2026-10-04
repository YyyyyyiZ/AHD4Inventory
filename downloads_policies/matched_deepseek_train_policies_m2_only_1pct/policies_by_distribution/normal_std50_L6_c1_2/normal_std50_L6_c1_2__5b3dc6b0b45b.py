# policy_hash: 5b3dc6b0b45b8691882d06ba48b80f26d0b8e77afa191a79a966f8c7fafde73a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5703.88
# best_prompt_performance: 5741.26
# best_rel_error_pct: 0.655343
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002122.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 532.6238472093423  # OPT_PARAM: {"initial": 532.6238472093423, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 98.67167706738141  # OPT_PARAM: {"initial": 98.67167706738141, "min": 0, "max": 300, "type": "float"}
    pipeline_weight = 1.1015579525486328  # OPT_PARAM: {"initial": 1.1015579525486328, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective pipeline inventory with weight
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate net inventory position
    net_position = on_hand_inventory + weighted_pipeline

    # Calculate order-up-to level with safety stock adjustment
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - net_position)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
