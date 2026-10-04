# policy_hash: ef9e0af20ff33b2ee8a9e9286bf4ffb76e880a85179c9231116d23bb35d64a38
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 4483.71
# best_prompt_performance: 4484.0
# best_rel_error_pct: 0.006468
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_013915.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 652.2127424452511  # OPT_PARAM: {"initial": 652.2127424452511, "min": 500, "max": 900, "type": "float"}
    safety_stock = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 30, "max": 120, "type": "float"}
    pipeline_weight = 0.6707719309684669  # OPT_PARAM: {"initial": 0.6707719309684669, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.15989409173706393  # OPT_PARAM: {"initial": 0.15989409173706393, "min": 0.1, "max": 0.5, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate weighted inventory position
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on immediate coverage
    immediate_coverage = on_hand_inventory + (pipeline_orders[0] if pipeline_orders else 0)
    adjusted_base = base_stock * demand_buffer if immediate_coverage < safety_stock else base_stock

    # Calculate order quantity
    base_order = max(0, adjusted_base - inventory_position)

    # Safety adjustment for immediate shortage
    safety_adjustment = max(0, safety_stock - immediate_coverage)

    # Combine with smoothing
    combined_order = smoothing_factor * base_order + (1 - smoothing_factor) * safety_adjustment

    # Round to nearest integer
    order_amount = int(round(combined_order))

    return order_amount
