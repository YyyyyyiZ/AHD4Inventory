# policy_hash: fea90b2849fc739c9090bd7305abe526c9ab47bd9631c0fb5e3244e6c1cbd4c7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 3794.39
# best_prompt_performance: 3794.32
# best_rel_error_pct: 0.001845
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_064742.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 818.1004321174315  # OPT_PARAM: {"initial": 818.1004321174315, "min": 700, "max": 1100, "type": "float"}
    safety_stock = 83.78381022635584  # OPT_PARAM: {"initial": 83.78381022635584, "min": 80, "max": 200, "type": "float"}
    demand_estimate = 90.58903252785991  # OPT_PARAM: {"initial": 90.58903252785991, "min": 90, "max": 120, "type": "float"}
    pipeline_weight = 0.6108835244753532  # OPT_PARAM: {"initial": 0.6108835244753532, "min": 0.5, "max": 1.0, "type": "float"}
    order_smoothing = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_correction = 0.45385422269517295  # OPT_PARAM: {"initial": 0.45385422269517295, "min": 0.1, "max": 0.5, "type": "float"}
    demand_adjustment = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.2, "type": "float"}
    smoothing_factor = 0.7346279152499974  # OPT_PARAM: {"initial": 0.7346279152499974, "min": 0.5, "max": 1.0, "type": "float"}

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

    # Target inventory position with demand adjustment
    target = base_stock * pipeline_factor + safety_stock

    # Calculate desired order
    desired_order = max(0, target - inventory_position)

    # Apply smoothing with adjusted demand estimate
    adjusted_demand = demand_estimate * demand_adjustment
    smoothed_order = order_smoothing * desired_order + (1 - order_smoothing) * adjusted_demand

    # Additional smoothing to reduce volatility
    final_order = smoothing_factor * smoothed_order + (1 - smoothing_factor) * adjusted_demand

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
