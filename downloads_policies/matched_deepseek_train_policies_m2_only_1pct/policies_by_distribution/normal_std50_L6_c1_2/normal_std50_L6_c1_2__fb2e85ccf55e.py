# policy_hash: fb2e85ccf55ec8d8570ccfe30e895c86d2fcef8b4ecc7ea4a281db834a26444c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 4349.02
# best_prompt_performance: 4351.54
# best_rel_error_pct: 0.057944
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_014004.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 616.1733617683678  # OPT_PARAM: {"initial": 616.1733617683678, "min": 500, "max": 750, "type": "float"}
    safety_stock = 39.76887942277539  # OPT_PARAM: {"initial": 39.76887942277539, "min": 25, "max": 80, "type": "float"}
    smoothing_factor = 0.1731392488931418  # OPT_PARAM: {"initial": 0.1731392488931418, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8403286521692506  # OPT_PARAM: {"initial": 0.8403286521692506, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 1.4432497426950552  # OPT_PARAM: {"initial": 1.4432497426950552, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with full pipeline consideration
    total_pipeline = sum(pipeline_orders)
    inventory_position = on_hand_inventory + total_pipeline

    # Adjust base stock based on demand buffer
    adjusted_base_stock = base_stock * demand_buffer

    # Base order calculation
    base_order = max(0, adjusted_base_stock - inventory_position)

    # Immediate coverage check with safety stock
    immediate_coverage = on_hand_inventory + (pipeline_orders[0] if pipeline_orders else 0)
    safety_adjustment = max(0, safety_stock - immediate_coverage)

    # Weighted combination
    combined_order = smoothing_factor * base_order + (1 - smoothing_factor) * safety_adjustment

    # Apply pipeline weight to final order
    final_order = combined_order * pipeline_weight

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
