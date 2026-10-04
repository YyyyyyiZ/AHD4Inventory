# policy_hash: 5d64de85059d5c64f8fd86791b5f5cf5c5d61709222b8fe5c1959ce27a58240e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2543.96
# best_prompt_performance: 2545.16
# best_rel_error_pct: 0.047171
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_025648.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 654.5360193498909  # OPT_PARAM: {"initial": 654.5360193498909, "min": 500, "max": 800, "type": "float"}
    safety_stock = 132.3672023732065  # OPT_PARAM: {"initial": 132.3672023732065, "min": 80, "max": 200, "type": "float"}
    demand_forecast_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.2, "type": "float"}
    pipeline_weight = 0.018061107742553126  # OPT_PARAM: {"initial": 0.018061107742553126, "min": 0.0, "max": 0.3, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lost_sales_weight = 2.877953777236077  # OPT_PARAM: {"initial": 2.877953777236077, "min": 1.5, "max": 3.0, "type": "float"}
    cost_ratio_factor = 1.441116394109802  # OPT_PARAM: {"initial": 1.441116394109802, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level considering cost ratio
    # p/h = 2, so we want to balance holding vs lost sales
    target_inventory = base_stock + safety_stock * (lost_sales_weight * cost_ratio_factor)

    # Adjust target based on pipeline variability
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_adjustment = pipeline_weight * avg_pipeline
        adjusted_target = target_inventory - pipeline_adjustment
    else:
        adjusted_target = target_inventory

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing
    smoothed_order = base_order * smoothing_factor

    # Apply demand forecast factor
    order_amount = int(round(smoothed_order * demand_forecast_factor))

    return order_amount
