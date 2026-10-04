# policy_hash: 9d54e44de8f899b65ef9e660989e1c1f0923eaf2db5f1d345655df1b6b7e4c75
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10167.72
# best_prompt_performance: 10167.69
# best_rel_error_pct: 0.000295
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233240.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 347.94763503262516  # OPT_PARAM: {"initial": 347.94763503262516, "min": 200, "max": 450, "type": "float"}
    safety_factor = 2.235657946135614  # OPT_PARAM: {"initial": 2.235657946135614, "min": 1.2, "max": 3.0, "type": "float"}
    smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.95, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate effective pipeline (weighted by arrival time)
    weighted_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = pipeline_weight ** (i + 1)  # Higher weight for sooner arrivals
        weighted_pipeline += q * weight

    # Calculate inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Dynamic safety stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_ratio = weighted_pipeline / pipeline_sum
    else:
        pipeline_ratio = 1.0

    # Adjust target based on pipeline characteristics
    dynamic_target = base_stock * (1 + safety_factor * (1 - pipeline_ratio))

    # Calculate order amount
    order_amount = max(0, dynamic_target - effective_inventory)

    # Apply smoothing
    if order_amount > 0:
        order_amount = smoothing * order_amount

    # Round to nearest integer
    return order_amount
