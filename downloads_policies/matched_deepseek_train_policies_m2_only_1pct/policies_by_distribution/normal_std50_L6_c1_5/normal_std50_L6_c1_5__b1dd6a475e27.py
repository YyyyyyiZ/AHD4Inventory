# policy_hash: b1dd6a475e275eaabc33410b48d722ccd04395d1b6d2c852eb20c9b737fde0da
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 6977.38
# best_prompt_performance: 6977.38
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_134753.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 674.9146025504903  # OPT_PARAM: {"initial": 674.9146025504903, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 137.10470871017148  # OPT_PARAM: {"initial": 137.10470871017148, "min": 50, "max": 300, "type": "float"}
    smoothing_factor = 0.301359787529633  # OPT_PARAM: {"initial": 0.301359787529633, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order-up-to level with safety stock adjustment
    desired_level = base_stock + safety_stock

    # Calculate order amount with smoothing to avoid large fluctuations
    raw_order = max(0, desired_level - inventory_position)
    order_amount = int(round(smoothing_factor * raw_order))

    return order_amount
