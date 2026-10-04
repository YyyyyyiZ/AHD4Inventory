# policy_hash: fd412557c8bf3d362e36477a2322ca83f4382d3fc89894950e0613832e88032b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5077.08
# best_prompt_performance: 5080.04
# best_rel_error_pct: 0.058301
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_011715.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 539.7547119838111  # OPT_PARAM: {"initial": 539.7547119838111, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 51.852712771004086  # OPT_PARAM: {"initial": 51.852712771004086, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.38240550048925503  # OPT_PARAM: {"initial": 0.38240550048925503, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate base order using base-stock policy
    base_order = max(0, base_stock - inventory_position)

    # Adjust for safety stock - order more if below safety level
    safety_adjustment = max(0, safety_stock - on_hand_inventory)

    # Smooth the order to avoid large fluctuations
    smoothed_order = smoothing_factor * base_order + (1 - smoothing_factor) * safety_adjustment

    # Round to nearest integer (as required by output type)
    order_amount = int(round(smoothed_order))

    return order_amount
