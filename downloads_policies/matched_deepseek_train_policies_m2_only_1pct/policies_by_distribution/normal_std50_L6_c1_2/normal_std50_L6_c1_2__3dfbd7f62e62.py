# policy_hash: 3dfbd7f62e62d0507f4410d24438d06a9c8112901a7ff487b5f96e1392225da2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 4078.45
# best_prompt_performance: 4078.45
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_174432.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 450, "type": "float"}
    safety_stock = 20.41825202149377  # OPT_PARAM: {"initial": 20.41825202149377, "min": 20, "max": 80, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    demand_estimate = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 150, "type": "float"}
    pipeline_coverage_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline coverage
    weighted_pipeline = 0
    total_weight = 0
    for i, qty in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += qty * weight
        total_weight += weight

    effective_pipeline = weighted_pipeline / total_weight if total_weight > 0 else 0

    # Improved target calculation with demand estimate
    target_inventory = base_stock + safety_stock + pipeline_coverage_factor * effective_pipeline + 0.2 * demand_estimate

    # Calculate order amount
    gap = target_inventory - inventory_position
    if gap > 0:
        # More aggressive ordering with dynamic upper bound
        max_order = order_multiplier * (demand_estimate + safety_stock / 2.0)
        order_amount = min(gap, max_order)
    else:
        order_amount = 0

    return order_amount
