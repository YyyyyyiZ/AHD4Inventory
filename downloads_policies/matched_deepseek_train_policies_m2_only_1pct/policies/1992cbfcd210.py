# policy_hash: 1992cbfcd2102c0eb90b3e3edca9272c5fa0cedba0b81ef920400f9f33c91de7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 36
# source_prompt_files: 2
# best_target_performance: 4127.44
# best_prompt_performance: 4124.14
# best_rel_error_pct: 0.079953
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_024626.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 465.8520472149571  # OPT_PARAM: {"initial": 465.8520472149571, "min": 400, "max": 700, "type": "float"}
    safety_stock = 70.8520472149531  # OPT_PARAM: {"initial": 70.8520472149531, "min": 20, "max": 150, "type": "float"}
    pipeline_adjustment = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount with pipeline adjustment
    order_amount = max(0, target_inventory - inventory_position * pipeline_adjustment)

    # Round to nearest integer
    return order_amount
