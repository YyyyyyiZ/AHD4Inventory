# policy_hash: 8d343bfa6e6c8214d13ed3b06883e635bfc52635f27ea5f964d54ac0e247e489
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 44
# source_prompt_files: 1
# best_target_performance: 835.06
# best_prompt_performance: 835.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_094906.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 531.4428962445122  # OPT_PARAM: {"initial": 531.4428962445122, "min": 400, "max": 700, "type": "float"}
    safety_stock = 146.25262886927646  # OPT_PARAM: {"initial": 146.25262886927646, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.19999999999999998  # OPT_PARAM: {"initial": 0.19999999999999998, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Base order with smoothing
    desired_order = max(0, base_stock - inventory_position)
    smoothed_order = smoothing_factor * desired_order

    # Dynamic safety stock adjustment based on imminent arrivals
    if pipeline_orders[0] > 0:
        # More safety when imminent arrival is low relative to average pipeline
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if avg_pipeline > 0:
            ratio = pipeline_orders[0] / avg_pipeline
            # Reduce safety when ratio is high (good imminent supply)
            safety_multiplier = max(0.5, 1.5 - ratio)
            safety_adjustment = safety_stock * safety_multiplier * (1.0 - pipeline_weight)
            smoothed_order += safety_adjustment

    # Add pipeline-weighted adjustment
    if len(pipeline_orders) > 1:
        # Focus on near-term pipeline coverage
        near_term = sum(pipeline_orders[:2])  # next two arrivals
        total_pipeline = sum(pipeline_orders)
        if total_pipeline > 0:
            coverage_ratio = near_term / total_pipeline
            # Order more if near-term coverage is low
            pipeline_adjustment = pipeline_weight * safety_stock * (1.0 - coverage_ratio)
            smoothed_order += pipeline_adjustment

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
