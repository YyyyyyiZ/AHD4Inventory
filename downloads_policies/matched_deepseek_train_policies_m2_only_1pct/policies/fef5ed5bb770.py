# policy_hash: fef5ed5bb770a26e9cdff9cca44b2a8fe034a7b2973bd7a9427cbf37048c555d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 5943.46
# best_prompt_performance: 5943.42
# best_rel_error_pct: 0.000673
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104923.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 152.17896321286176  # OPT_PARAM: {"initial": 152.17896321286176, "min": 50, "max": 300, "type": "float"}
    safety_stock = 62.178963212861625  # OPT_PARAM: {"initial": 62.178963212861625, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.19582104902066008  # OPT_PARAM: {"initial": 0.19582104902066008, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple target calculation without demand forecasting
    target_inventory = base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing using last order if available
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
