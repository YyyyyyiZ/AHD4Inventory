# policy_hash: d156f4c306ab03a38a92d693c310d8d50e812b121e016c70a8c95f4fb1544230
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 5040.29
# best_prompt_performance: 5048.58
# best_rel_error_pct: 0.164475
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002546.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 506.95349118073915  # OPT_PARAM: {"initial": 506.95349118073915, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 23.00132103877371  # OPT_PARAM: {"initial": 23.00132103877371, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0005557455767797  # OPT_PARAM: {"initial": 1.0005557455767797, "min": 0.1, "max": 1.5, "type": "float"}
    inventory_weight = 0.5084886645395714  # OPT_PARAM: {"initial": 0.5084886645395714, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate effective pipeline (weighted sum)
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                          for i, p in enumerate(pipeline_orders))

    # Calculate inventory position with different weights
    inventory_position = (inventory_weight * on_hand_inventory +
                         weighted_pipeline)

    # Adjust base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Order amount calculation
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
