# policy_hash: bbd424fd0b435358c81f46fbb22286d5ce4475c51d746cd7ae5e8cfc42602b4a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4432.98
# best_prompt_performance: 4427.06
# best_rel_error_pct: 0.133544
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_013856.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 602.6953933728288  # OPT_PARAM: {"initial": 602.6953933728288, "min": 550, "max": 750, "type": "float"}
    safety_stock = 81.07916997188454  # OPT_PARAM: {"initial": 81.07916997188454, "min": 70, "max": 120, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 1.0531464863029256  # OPT_PARAM: {"initial": 1.0531464863029256, "min": 1.0, "max": 1.3, "type": "float"}
    smoothing_factor = 0.47907288976070217  # OPT_PARAM: {"initial": 0.47907288976070217, "min": 0.2, "max": 0.5, "type": "float"}

    # Calculate effective inventory position with discounted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on demand buffer
    adjusted_base_stock = base_stock * demand_buffer

    # Calculate immediate coverage (inventory available for current period)
    immediate_coverage = on_hand_inventory + (pipeline_orders[0] if pipeline_orders else 0)

    # Base order from inventory position policy
    base_order = max(0, adjusted_base_stock - inventory_position)

    # Safety adjustment based on immediate coverage
    safety_adjustment = max(0, safety_stock - immediate_coverage)

    # Dynamic weighting based on immediate coverage
    if immediate_coverage < safety_stock:
        # When immediate coverage is low, prioritize safety
        combined_order = 0.8 * safety_adjustment + 0.2 * base_order
    else:
        # Normal operation: blend base order with safety considerations
        combined_order = smoothing_factor * base_order + (1 - smoothing_factor) * safety_adjustment

    # Round to nearest integer
    order_amount = int(round(combined_order))

    return order_amount
