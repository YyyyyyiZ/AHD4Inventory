# policy_hash: c42bb46fa19fcd91c9e1f06d34799f63706fb370fed50127018ba71c9b007648
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 11400.84
# best_prompt_performance: 11400.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004207.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 318.7994116977407  # OPT_PARAM: {"initial": 318.7994116977407, "min": 100, "max": 600, "type": "float"}
    safety_stock = 78.79941169774041  # OPT_PARAM: {"initial": 78.79941169774041, "min": 20, "max": 200, "type": "float"}
    demand_buffer = 28.799411697740485  # OPT_PARAM: {"initial": 28.799411697740485, "min": 10, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base stock policy with safety stock adjustment
    target_inventory = base_stock + safety_stock + demand_buffer

    # Calculate order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply simple smoothing based on pipeline average
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    if pipeline_orders:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * avg_past_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
