# policy_hash: baeeacdbac0d8ed975b46537dd280316673c4381f62040ee0ca0e9be5543d9d7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 838.88
# best_prompt_performance: 839.4
# best_rel_error_pct: 0.061987
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_233546.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 385.1105110092786  # OPT_PARAM: {"initial": 385.1105110092786, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 129.8467667781564  # OPT_PARAM: {"initial": 129.8467667781564, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.30091281203209563  # OPT_PARAM: {"initial": 0.30091281203209563, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall with adjustment
    expected_shortfall = max(0, base_stock - inventory_position)

    # Apply safety stock adjustment
    adjusted_shortfall = expected_shortfall + safety_stock

    # Smooth ordering with adjustment factor
    order_amount = max(0, adjustment_factor * adjusted_shortfall)

    return order_amount
