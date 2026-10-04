# policy_hash: 3a792d6d2a2baf38974f88ec9c06d4df0faf6153131e59984753fa5e312b0a2b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1515.06
# best_prompt_performance: 1515.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235408.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 472.78448366679226  # OPT_PARAM: {"initial": 472.78448366679226, "min": 400, "max": 600, "type": "float"}
    demand_estimate = 90.1  # OPT_PARAM: {"initial": 90.1, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Base order-up-to level adjustment
    base_order = max(0, base_stock - inventory_position)

    # Pipeline-aware adjustment: reduce order if pipeline is high
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = -pipeline_weight * max(0, avg_pipeline - demand_estimate)

    # Combine base order with pipeline adjustment
    raw_order = max(0, base_order + pipeline_adjustment)

    # Apply smoothing: blend with demand estimate
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
