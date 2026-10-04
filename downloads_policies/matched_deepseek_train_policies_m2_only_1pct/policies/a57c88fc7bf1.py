# policy_hash: a57c88fc7bf19f70cbee7cb9e072fdfeb7b836da8452d9e6bb36d246cb4638c6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1335.36
# best_prompt_performance: 1345.28
# best_rel_error_pct: 0.742871
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_024005.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 541.7032168476196  # OPT_PARAM: {"initial": 541.7032168476196, "min": 350, "max": 550, "type": "float"}
    safety_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 0.580290246308194  # OPT_PARAM: {"initial": 0.580290246308194, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = pipeline_weight * sum(pipeline_orders)

    # Adjust target based on pipeline coverage
    adjusted_target = base_stock + safety_factor * (base_stock - effective_pipeline)

    # Calculate order needed
    order_needed = max(0, adjusted_target - inventory_position)

    # Apply smoothing to prevent overshooting
    smoothed_order = smoothing_factor * order_needed

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
