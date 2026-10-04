# policy_hash: 918f77ca721a233a7ec69c111f9617b24ea4d4e05cb83dee3e49e5a2d7385b8a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 5945.84
# best_prompt_performance: 5945.78
# best_rel_error_pct: 0.001009
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223910.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 100, "max": 300, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 100, "type": "float"}
    demand_smoothing = 0.061483175441321154  # OPT_PARAM: {"initial": 0.061483175441321154, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    # Weight recent pipeline orders more heavily
    weighted_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight
        total_weight += weight

    if total_weight > 0:
        effective_pipeline = weighted_pipeline / total_weight
    else:
        effective_pipeline = 0

    # Adjust base stock based on pipeline coverage
    # Less adjustment when pipeline is already substantial
    pipeline_adjustment = demand_smoothing * (base_stock - effective_pipeline)
    adjusted_base_stock = base_stock - pipeline_adjustment

    # Apply safety stock floor
    target_inventory = max(adjusted_base_stock, safety_stock)

    # Calculate order amount with smoother adjustment
    order_gap = target_inventory - inventory_position
    if order_gap > 0:
        order_amount = order_gap * adjustment_factor
    else:
        order_amount = 0

    # Round to nearest integer (maintain non-negative)
    order_amount = max(0, int(round(order_amount)))

    return order_amount
