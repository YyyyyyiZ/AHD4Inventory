# policy_hash: bb4cc406f7df93905deee3ad519028061e7fb2d0feda57967795b2c40c3ec255
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 118
# source_prompt_files: 1
# best_target_performance: 3822.56
# best_prompt_performance: 3822.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_064259.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 819.1241202436639  # OPT_PARAM: {"initial": 819.1241202436639, "min": 700, "max": 1100, "type": "float"}
    safety_stock = 84.22919700264708  # OPT_PARAM: {"initial": 84.22919700264708, "min": 80, "max": 200, "type": "float"}
    demand_estimate = 90.76305155527754  # OPT_PARAM: {"initial": 90.76305155527754, "min": 90, "max": 120, "type": "float"}
    pipeline_weight = 0.6074324217262319  # OPT_PARAM: {"initial": 0.6074324217262319, "min": 0.5, "max": 1.0, "type": "float"}
    order_smoothing = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_correction = 0.4886595234600061  # OPT_PARAM: {"initial": 0.4886595234600061, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline for adjustment
    weighted_pipeline = 0.0
    total_pipeline = 0.0
    for i, p in enumerate(pipeline_orders):
        weight = pipeline_weight ** i
        weighted_pipeline += p * weight
        total_pipeline += p

    # Pipeline adjustment with correction factor
    if total_pipeline > 0:
        pipeline_factor = weighted_pipeline / total_pipeline
        # Apply correction to reduce over-reaction to pipeline
        pipeline_factor = 1.0 + pipeline_correction * (pipeline_factor - 1.0)
    else:
        pipeline_factor = 1.0

    # Target inventory position
    target = base_stock * pipeline_factor + safety_stock

    # Calculate desired order
    desired_order = max(0, target - inventory_position)

    # Apply smoothing with demand estimate as baseline
    smoothed_order = order_smoothing * desired_order + (1 - order_smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
