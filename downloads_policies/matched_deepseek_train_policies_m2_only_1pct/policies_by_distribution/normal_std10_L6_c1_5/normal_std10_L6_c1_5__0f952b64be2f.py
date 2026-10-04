# policy_hash: 0f952b64be2fd1458267b6dfb45f50f9b5c3192c5796cf54d92b31b8aacffa23
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1745.32
# best_prompt_performance: 1746.66
# best_rel_error_pct: 0.076777
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_084737.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 700.6307314919912  # OPT_PARAM: {"initial": 700.6307314919912, "min": 650, "max": 750, "type": "float"}
    safety_stock = 57.9085885179097  # OPT_PARAM: {"initial": 57.9085885179097, "min": 30, "max": 60, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 15, "max": 35, "type": "float"}
    pipeline_threshold = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    adjustment_strength = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 20, "type": "int"}
    max_order = 140  # OPT_PARAM: {"initial": 140, "min": 100, "max": 200, "type": "int"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    pipeline_cap = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 100, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (capped)
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        effective_pipeline = min(avg_pipeline, pipeline_cap)
    else:
        effective_pipeline = 0

    # Adjust base stock based on pipeline level
    if effective_pipeline > pipeline_threshold:
        adjustment = pipeline_weight * adjustment_strength
    else:
        adjustment = 1.0

    # Target inventory position with smoothing
    target_position = base_stock + safety_stock + demand_buffer
    smoothed_target = (target_position * smoothing_factor) + (inventory_position * (1 - smoothing_factor))

    # Calculate order amount with adjustment and smoothing
    order_amount = max(0, (smoothed_target - inventory_position) * adjustment)

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
