# policy_hash: d9b79f9caf28f82e1751d51d58847dd71932cbbe14975c274ee7df434082c513
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3874.47
# best_prompt_performance: 3874.47
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_180023.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.0  # OPT_PARAM: {"initial": 350.0, "min": 200, "max": 350, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 30, "max": 60, "type": "float"}
    pipeline_coverage = 0.6177919789164404  # OPT_PARAM: {"initial": 0.6177919789164404, "min": 0.6, "max": 0.9, "type": "float"}
    demand_estimate = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 120, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    lost_sales_weight = 1.520704266611489  # OPT_PARAM: {"initial": 1.520704266611489, "min": 1.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage

    # Adjust base stock based on lost sales cost weight
    adjusted_base_stock = base_stock * (lost_sales_weight / 2.0)

    # Target inventory calculation with stronger emphasis on preventing stockouts
    target_inventory = adjusted_base_stock + safety_stock + effective_pipeline

    # Calculate order amount
    gap = target_inventory - inventory_position
    if gap > 0:
        # Use demand estimate with multiplier, but ensure we cover at least one period's demand
        min_order = demand_estimate * 0.8
        max_order = order_multiplier * demand_estimate
        order_amount = max(min_order, min(gap, max_order))
    else:
        order_amount = 0

    return order_amount
