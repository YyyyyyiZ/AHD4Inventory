# policy_hash: 892c502341002af49a617fd4f4d5f25e01100b61a1ea323a01e32afec5c90e6d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 4210.05
# best_prompt_performance: 4208.4
# best_rel_error_pct: 0.039192
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_010004.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 516.2630691258739  # OPT_PARAM: {"initial": 516.2630691258739, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 59.20660296033596  # OPT_PARAM: {"initial": 59.20660296033596, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.5115601471608361  # OPT_PARAM: {"initial": 0.5115601471608361, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    order_needed = target_inventory - inventory_position
    smoothed_order = smoothing_factor * order_needed

    # Ensure non-negative order
    order_amount = max(0, smoothed_order)

    # Round to nearest integer for practical ordering
    return order_amount
