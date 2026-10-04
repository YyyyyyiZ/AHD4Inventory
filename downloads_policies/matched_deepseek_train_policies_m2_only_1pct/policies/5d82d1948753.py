# policy_hash: 5d82d19487533be3fff96b26a9544238ce33958fab94b0aed5ea3334f70f37c5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 12279.78
# best_prompt_performance: 12279.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_102139.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 413.012939055941  # OPT_PARAM: {"initial": 413.012939055941, "min": 300, "max": 600, "type": "float"}
    safety_factor = 1.1858900353166193  # OPT_PARAM: {"initial": 1.1858900353166193, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory with safety factor
    target_inventory = base_stock * safety_factor

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply exponential smoothing to reduce order volatility
    if pipeline_orders:
        # Use the most recent order as reference
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing * order_amount + (1 - smoothing) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
