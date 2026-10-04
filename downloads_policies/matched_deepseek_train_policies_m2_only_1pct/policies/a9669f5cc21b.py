# policy_hash: a9669f5cc21b20afa039a867c3f758720f1db169d8fe5ac03957f50320a0bc4a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 2
# best_target_performance: 1682.66
# best_prompt_performance: 1682.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034229.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 505.61187626913744  # OPT_PARAM: {"initial": 505.61187626913744, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 171.60348039995665  # OPT_PARAM: {"initial": 171.60348039995665, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_std = 0.0
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((x - pipeline_mean) ** 2 for x in pipeline_orders) / len(pipeline_orders)) ** 0.5

    # Dynamic adjustment based on pipeline variability
    variability_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0, "max": 0.5, "type": "float"}
    adjusted_base_stock = base_stock * variability_adjustment

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1] if pipeline_orders else raw_order

    # Round to nearest integer (as order amount should be integer)
    order_amount = int(round(smoothed_order))

    return order_amount
