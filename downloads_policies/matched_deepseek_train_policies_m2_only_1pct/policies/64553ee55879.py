# policy_hash: 64553ee55879009cbfd2f7b75041cca66aecbd78c7ed504de1c5b350c2e5ddd2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 4751.81
# best_prompt_performance: 4746.22
# best_rel_error_pct: 0.117639
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_011736.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 619.8139295351049  # OPT_PARAM: {"initial": 619.8139295351049, "min": 500, "max": 750, "type": "float"}
    safety_stock = 80.25101462243053  # OPT_PARAM: {"initial": 80.25101462243053, "min": 50, "max": 120, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.3, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.2, "max": 0.5, "type": "float"}

    # Calculate effective inventory position with discounted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on immediate coverage risk
    immediate_coverage = on_hand_inventory + pipeline_orders[0] if pipeline_orders else on_hand_inventory
    adjusted_base_stock = base_stock * demand_buffer

    # Calculate order using modified base-stock policy
    base_order = max(0, adjusted_base_stock - inventory_position)

    # Safety stock adjustment for immediate shortage prevention
    safety_adjustment = max(0, safety_stock - immediate_coverage)

    # Combine with emphasis on safety when immediate coverage is low
    if immediate_coverage < safety_stock:
        combined_order = 0.7 * safety_adjustment + 0.3 * base_order
    else:
        combined_order = smoothing_factor * base_order + (1 - smoothing_factor) * safety_adjustment

    # Round to nearest integer
    order_amount = int(round(combined_order))

    return order_amount
