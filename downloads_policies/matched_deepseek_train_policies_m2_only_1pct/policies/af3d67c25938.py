# policy_hash: af3d67c25938e38178248657511c70ca41366d4a7a47fe4b4d7d799e6b718b49
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 3165.92
# best_prompt_performance: 3165.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_051632.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 700.9700474060967  # OPT_PARAM: {"initial": 700.9700474060967, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.06977500647338  # OPT_PARAM: {"initial": 58.06977500647338, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.5609302909775788  # OPT_PARAM: {"initial": 0.5609302909775788, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position with safety stock
    target_inventory = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    order_amount = max(0, smoothing_factor * (target_inventory - inventory_position))

    # Round to nearest integer since order amount should be integer
    return order_amount
