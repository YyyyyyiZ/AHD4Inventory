# policy_hash: 1843ab34c4e2ae6970f0c3a790d25582ee710c484fc8cc37b82879937488b7db
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5892.76
# best_prompt_performance: 5892.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065836.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 184.45536333082325  # OPT_PARAM: {"initial": 184.45536333082325, "min": 100, "max": 300, "type": "float"}
    safety_stock = 74.45529744431057  # OPT_PARAM: {"initial": 74.45529744431057, "min": 30, "max": 150, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3562801966312264  # OPT_PARAM: {"initial": 0.3562801966312264, "min": 0.2, "max": 0.7, "type": "float"}
    demand_buffer = 1.2185781104989344  # OPT_PARAM: {"initial": 1.2185781104989344, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target based on pipeline and safety stock
    pipeline_adjustment = sum(pipeline_orders) * (1 - pipeline_weight)
    target_inventory = base_stock * demand_buffer + safety_stock - pipeline_adjustment

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > base_stock * 0.05:
        smoothed_order = raw_order * smoothing_factor + (base_stock * 0.08) * (1 - smoothing_factor)
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
