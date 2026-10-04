# policy_hash: c653eaa0c0c55eb0b2e994ba87d1c72a2d467c4adda4163eab20265e2b93677b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 61
# source_prompt_files: 2
# best_target_performance: 11390.49
# best_prompt_performance: 11390.49
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_062003.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.7433578831464  # OPT_PARAM: {"initial": 449.7433578831464, "min": 300, "max": 600, "type": "float"}
    safety_stock = 179.6920312220504  # OPT_PARAM: {"initial": 179.6920312220504, "min": 100, "max": 300, "type": "float"}
    pipeline_coverage = 0.926154853819998  # OPT_PARAM: {"initial": 0.926154853819998, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.18584256156303955  # OPT_PARAM: {"initial": 0.18584256156303955, "min": 0.1, "max": 0.5, "type": "float"}
    demand_multiplier = 1.2448453592838211  # OPT_PARAM: {"initial": 1.2448453592838211, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    # Weight older pipeline orders more heavily since they arrive sooner
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = (len(pipeline_orders) - i) / len(pipeline_orders)
        weighted_pipeline += order * weight

    # Target inventory position based on base stock and safety stock
    target_inventory = base_stock + safety_stock * demand_multiplier

    # Calculate order needed to reach target
    # Account for weighted pipeline coverage
    net_order = target_inventory - inventory_position + pipeline_coverage * weighted_pipeline

    # Apply smoothing to avoid extreme order fluctuations
    if net_order > 0:
        order_amount = net_order * smoothing_factor
    else:
        order_amount = 0

    # Round to nearest integer (non-negative)
    return order_amount
