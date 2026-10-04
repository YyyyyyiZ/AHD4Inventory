# policy_hash: df2884e0e8335ccdbc1f72370e3da0729dc5ccd33a8ee515f01ad3052144a0d6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 2781.11
# best_prompt_performance: 2781.11
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015546.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 638.9724687230938  # OPT_PARAM: {"initial": 638.9724687230938, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.98291948493397  # OPT_PARAM: {"initial": 24.98291948493397, "min": 0, "max": 200, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level with safety stock adjustment
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    return order_amount
