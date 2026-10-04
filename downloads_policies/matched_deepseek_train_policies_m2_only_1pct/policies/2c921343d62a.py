# policy_hash: 2c921343d62a636df5ccf1d30e669b685a77141a3f1866c5340aafa9f508942a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 796.75
# best_prompt_performance: 798.74
# best_rel_error_pct: 0.249765
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_230831.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.00000000007924  # OPT_PARAM: {"initial": 380.00000000007924, "min": 380, "max": 460, "type": "float"}
    safety_stock = 20.000000000011912  # OPT_PARAM: {"initial": 20.000000000011912, "min": 20, "max": 50, "type": "float"}
    demand_estimate = 95.01635630186244  # OPT_PARAM: {"initial": 95.01635630186244, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    adjustment_factor = 0.020605903858549945  # OPT_PARAM: {"initial": 0.020605903858549945, "min": 0, "max": 20, "type": "float"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Use weighted pipeline
    weighted_pipeline = pipeline_weight * total_pipeline

    # Inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Order-up-to level with adjustment
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand estimate
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Add adjustment factor for responsiveness
    final_order = smoothed_order + adjustment_factor

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
