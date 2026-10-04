# policy_hash: fd24475e36aeee0470ff476b75acb4f9ce9175ba6a3133e02e6dc05fc0630583
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 4345.32
# best_prompt_performance: 4345.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_173912.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 450, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 80, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

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

    # Simplified target calculation
    target_inventory = base_stock + safety_stock + 0.3 * effective_pipeline

    # Calculate order amount
    gap = target_inventory - inventory_position
    if gap > 0:
        # Smooth ordering with upper bound
        max_order = order_multiplier * (base_stock / 4.0)
        order_amount = min(gap, max_order)
    else:
        order_amount = 0

    return order_amount
