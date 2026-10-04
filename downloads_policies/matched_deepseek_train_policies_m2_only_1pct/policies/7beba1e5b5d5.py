# policy_hash: 7beba1e5b5d5c550c9aa3e7881e2e18b0061314867121c19a1cc9ed030588324
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 10168.94
# best_prompt_performance: 10168.85
# best_rel_error_pct: 0.000885
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233034.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 413.06318660668325  # OPT_PARAM: {"initial": 413.06318660668325, "min": 200, "max": 600, "type": "float"}
    safety_stock = 18.06318660668181  # OPT_PARAM: {"initial": 18.06318660668181, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.38952503428541363  # OPT_PARAM: {"initial": 0.38952503428541363, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position
    target = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
