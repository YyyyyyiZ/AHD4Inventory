# policy_hash: 10092a7d30a0a03992c00dfd0b45ba8419bc3ba725b4076659c64a4a8fa0dbb8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 11655.54
# best_prompt_performance: 11655.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060438.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.6354610236937  # OPT_PARAM: {"initial": 480.6354610236937, "min": 100, "max": 800, "type": "float"}
    safety_stock = 110.6354610237035  # OPT_PARAM: {"initial": 110.6354610237035, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.6393491338160803  # OPT_PARAM: {"initial": 0.6393491338160803, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic order-up-to level based on pipeline variability
    pipeline_std = 0.0
    if len(pipeline_orders) > 1:
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((x - mean_pipeline) ** 2 for x in pipeline_orders) / len(pipeline_orders)) ** 0.5

    # Adjust safety stock based on pipeline variability
    variability_adjustment = 0.4942364491966161  # OPT_PARAM: {"initial": 0.4942364491966161, "min": 0.1, "max": 0.8, "type": "float"}
    adjusted_safety = safety_stock + variability_adjustment

    # Calculate order-up-to level
    order_up_to = base_stock + adjusted_safety

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0.0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
