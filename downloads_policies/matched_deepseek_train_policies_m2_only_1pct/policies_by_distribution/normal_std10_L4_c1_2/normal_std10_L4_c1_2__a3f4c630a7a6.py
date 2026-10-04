# policy_hash: a3f4c630a7a6dcb2639390da3f51d06b611d5bf2703a375b209c65c4f4a8e91e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 791.72
# best_prompt_performance: 791.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_100041.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 586.7704981917827  # OPT_PARAM: {"initial": 586.7704981917827, "min": 500, "max": 750, "type": "float"}
    safety_stock = 74.92728825890225  # OPT_PARAM: {"initial": 74.92728825890225, "min": 60, "max": 120, "type": "float"}
    smoothing_factor = 0.14021438643301581  # OPT_PARAM: {"initial": 0.14021438643301581, "min": 0.1, "max": 0.4, "type": "float"}
    pipeline_weight = 0.30808347805858893  # OPT_PARAM: {"initial": 0.30808347805858893, "min": 0.2, "max": 0.6, "type": "float"}
    imminent_weight = 0.6465645343439056  # OPT_PARAM: {"initial": 0.6465645343439056, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 1.0098557113784734  # OPT_PARAM: {"initial": 1.0098557113784734, "min": 1.0, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjusted base stock based on demand buffer
    adjusted_base_stock = base_stock * demand_buffer

    # Base order with smoothing
    desired_order = max(0, adjusted_base_stock - inventory_position)
    smoothed_order = smoothing_factor * desired_order

    # Dynamic safety stock adjustment based on imminent arrivals
    if pipeline_orders[0] > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if avg_pipeline > 0:
            ratio = pipeline_orders[0] / avg_pipeline
            # More aggressive adjustment for imminent arrivals
            safety_multiplier = max(0.3, 1.7 - ratio * imminent_weight)
            safety_adjustment = safety_stock * safety_multiplier * (1.0 - pipeline_weight)
            smoothed_order += safety_adjustment

    # Add pipeline-weighted adjustment
    if len(pipeline_orders) > 1:
        near_term = sum(pipeline_orders[:2])
        total_pipeline = sum(pipeline_orders)
        if total_pipeline > 0:
            coverage_ratio = near_term / total_pipeline
            # Stronger adjustment for pipeline coverage
            pipeline_adjustment = pipeline_weight * safety_stock * (1.2 - coverage_ratio)
            smoothed_order += pipeline_adjustment

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
