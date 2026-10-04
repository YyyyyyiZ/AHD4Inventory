# policy_hash: ad0e76d7ddcb355ec060e67fa70270ed008661467bc05dc75c8e08dfced94acd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 37
# source_prompt_files: 1
# best_target_performance: 2401.8
# best_prompt_performance: 2402.6
# best_rel_error_pct: 0.033308
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_030338.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.4335952502729  # OPT_PARAM: {"initial": 600.4335952502729, "min": 400, "max": 800, "type": "float"}
    safety_stock = 100.8131239662459  # OPT_PARAM: {"initial": 100.8131239662459, "min": 50, "max": 200, "type": "float"}
    demand_forecast_factor = 0.9109543717027815  # OPT_PARAM: {"initial": 0.9109543717027815, "min": 0.6, "max": 1.2, "type": "float"}
    pipeline_weight = 0.034160237819979164  # OPT_PARAM: {"initial": 0.034160237819979164, "min": 0.0, "max": 0.3, "type": "float"}
    smoothing_factor = 0.41327672744474625  # OPT_PARAM: {"initial": 0.41327672744474625, "min": 0.1, "max": 0.8, "type": "float"}
    lost_sales_weight = 2.6396918123033744  # OPT_PARAM: {"initial": 2.6396918123033744, "min": 1.5, "max": 3.0, "type": "float"}
    cost_ratio_factor = 1.2892557710243997  # OPT_PARAM: {"initial": 1.2892557710243997, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_variability_factor = 0.05870251241856959  # OPT_PARAM: {"initial": 0.05870251241856959, "min": 0.0, "max": 0.5, "type": "float"}
    demand_smoothing = 0.5276433587238263  # OPT_PARAM: {"initial": 0.5276433587238263, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline variability adjustment
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variance = sum((q - avg_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        variability_adjustment = pipeline_variability_factor * pipeline_variance
    else:
        variability_adjustment = 0

    # Calculate target inventory with cost optimization
    # p/h = 2, so optimal service level = p/(p+h) = 2/3 ≈ 0.667
    target_inventory = base_stock + safety_stock * (lost_sales_weight * cost_ratio_factor) - variability_adjustment

    # Adjust for pipeline (reduce target when pipeline is high)
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_adjustment = pipeline_weight * avg_pipeline
        adjusted_target = target_inventory - pipeline_adjustment
    else:
        adjusted_target = target_inventory

    # Calculate base order with demand smoothing
    base_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing with demand consideration
    smoothed_order = base_order * smoothing_factor

    # Apply demand forecast and final smoothing
    order_amount = int(round(smoothed_order * demand_forecast_factor * demand_smoothing))

    return order_amount
