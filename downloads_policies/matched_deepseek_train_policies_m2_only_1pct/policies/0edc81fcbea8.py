# policy_hash: 0edc81fcbea8358b32bad5658b5adce5a298580c76f42b46dfd82c64b924cf99
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2979.08
# best_prompt_performance: 2969.92
# best_rel_error_pct: 0.307477
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_024933.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 577.560206682915  # OPT_PARAM: {"initial": 577.560206682915, "min": 500, "max": 650, "type": "float"}
    safety_stock = 41.81793369598313  # OPT_PARAM: {"initial": 41.81793369598313, "min": 30, "max": 60, "type": "float"}
    pipeline_coverage = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    pipeline_discount_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline with time-based discounting
    weighted_pipeline = 0.0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_discount_factor ** i
        weighted_pipeline += order * weight

    # Calculate effective inventory position
    effective_pipeline = weighted_pipeline * pipeline_coverage
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic safety adjustment based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variance = sum((x - pipeline_mean) ** 2 for x in pipeline_orders) / len(pipeline_orders)
        pipeline_std = pipeline_variance ** 0.5
        safety_adjustment = min(1.5, max(0.5, 1.0 + pipeline_std / 100.0))
        adjusted_safety = safety_stock * safety_adjustment
    else:
        adjusted_safety = safety_stock

    # Calculate target level
    target_level = base_stock + adjusted_safety

    # Raw order needed
    raw_order_needed = max(0, target_level - inventory_position)

    # Apply exponential smoothing
    smoothed_order = smoothing_factor * raw_order_needed

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
