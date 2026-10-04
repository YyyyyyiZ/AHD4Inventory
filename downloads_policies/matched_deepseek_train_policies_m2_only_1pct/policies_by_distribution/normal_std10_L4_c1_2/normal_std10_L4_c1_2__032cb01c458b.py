# policy_hash: 032cb01c458bbd3eb433c557c4575c601ff37f88646491285fc2b28f009b208c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1272.16
# best_prompt_performance: 1273.0
# best_rel_error_pct: 0.066029
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_025633.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 497.77574931577226  # OPT_PARAM: {"initial": 497.77574931577226, "min": 400, "max": 550, "type": "float"}
    safety_factor = 0.8449773419363393  # OPT_PARAM: {"initial": 0.8449773419363393, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 0.6119531673274238  # OPT_PARAM: {"initial": 0.6119531673274238, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lead_time_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    demand_adjustment = 0.9866623622180285  # OPT_PARAM: {"initial": 0.9866623622180285, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate weighted pipeline with emphasis on near-term arrivals
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = lead_time_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += weight * order

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = pipeline_weight * weighted_pipeline

    # Adjust target based on pipeline coverage and demand adjustment
    adjusted_target = base_stock * demand_adjustment + safety_factor * (base_stock - effective_pipeline)

    # Calculate order needed
    order_needed = max(0, adjusted_target - inventory_position)

    # Apply smoothing to prevent overshooting
    smoothed_order = smoothing_factor * order_needed

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
