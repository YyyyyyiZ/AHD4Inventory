# policy_hash: 88c232b122ba4395905ded148516408da730c2ef9e5d9f459c8e4289064a6a19
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 18
# source_prompt_files: 2
# best_target_performance: 3820.99
# best_prompt_performance: 3822.77
# best_rel_error_pct: 0.046585
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_012439.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 568.6336276142663  # OPT_PARAM: {"initial": 568.6336276142663, "min": 400, "max": 800, "type": "float"}
    safety_stock = 35.30738859451215  # OPT_PARAM: {"initial": 35.30738859451215, "min": 20, "max": 100, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Base order from base-stock policy
    base_order = max(0, base_stock - inventory_position)

    # Safety adjustment based on immediate coverage
    immediate_coverage = on_hand_inventory + pipeline_orders[0] if pipeline_orders else on_hand_inventory
    safety_adjustment = max(0, safety_stock - immediate_coverage)

    # Combine with smoothing
    combined_order = smoothing_factor * base_order + (1 - smoothing_factor) * safety_adjustment

    # Round to nearest integer
    order_amount = int(round(combined_order))

    return order_amount
