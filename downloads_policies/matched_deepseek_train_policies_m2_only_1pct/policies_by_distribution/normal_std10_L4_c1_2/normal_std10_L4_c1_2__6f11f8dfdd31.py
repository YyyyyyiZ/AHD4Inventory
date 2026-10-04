# policy_hash: 6f11f8dfdd314138f78d9a2b12ad0439e4a2e07758ee6228dd18d70dc693163b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1251.8
# best_prompt_performance: 1251.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_094039.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 525.2901711135387  # OPT_PARAM: {"initial": 525.2901711135387, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 91.31781188958558  # OPT_PARAM: {"initial": 91.31781188958558, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order amount with base stock policy
    desired_order = max(0, base_stock - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    smoothed_order = smoothing_factor * desired_order

    # Add safety stock adjustment based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_ratio = pipeline_orders[0] / pipeline_sum if pipeline_sum > 0 else 1.0
        safety_adjustment = safety_stock * (1.0 - pipeline_ratio)
        smoothed_order += safety_adjustment

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(smoothed_order))

    return order_amount
