# policy_hash: 729669acc2b45d8729d79866a28d6cd9497230da84526d8e80dd0506efb25756
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2693.24
# best_prompt_performance: 2693.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_061105.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 923.6067389882835  # OPT_PARAM: {"initial": 923.6067389882835, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 177.29576145337046  # OPT_PARAM: {"initial": 177.29576145337046, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.08929796952153618  # OPT_PARAM: {"initial": 0.08929796952153618, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate base order using base-stock policy
    base_order = max(0, base_stock - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * base_order

    # Add safety stock adjustment
    if inventory_position < base_stock - safety_stock:
        safety_adjustment = safety_stock * (1 - inventory_position / base_stock)
    else:
        safety_adjustment = 0

    # Final order amount
    order_amount = max(0, smoothed_order + safety_adjustment)

    # Round to nearest integer (as required by problem statement)
    return order_amount
