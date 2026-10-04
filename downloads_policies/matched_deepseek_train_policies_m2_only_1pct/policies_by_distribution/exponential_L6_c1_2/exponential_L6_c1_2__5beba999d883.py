# policy_hash: 5beba999d8836cadef0fadc1c42bc65b7d0dc5e1d1beda8412aa3f11c66aa6d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 6026.81
# best_prompt_performance: 6026.81
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055023.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 529.3291447304567  # OPT_PARAM: {"initial": 529.3291447304567, "min": 300, "max": 800, "type": "float"}
    safety_stock = 102.89187558115438  # OPT_PARAM: {"initial": 102.89187558115438, "min": 50, "max": 250, "type": "float"}
    pipeline_weight = 0.7676783297230458  # OPT_PARAM: {"initial": 0.7676783297230458, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    demand_buffer = 1.344647149547839  # OPT_PARAM: {"initial": 1.344647149547839, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate effective pipeline
    total_pipeline = sum(pipeline_orders)
    effective_pipeline = total_pipeline * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on demand buffer
    adjusted_base_stock = base_stock * demand_buffer

    # Calculate target level
    target_level = adjusted_base_stock + safety_stock

    # Calculate order needed
    order_needed = target_level - inventory_position

    # Apply smoothing and ensure non-negative
    if order_needed > 0:
        order_amount = max(0, smoothing_factor * order_needed)
    else:
        order_amount = 0

    return order_amount
