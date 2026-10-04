# policy_hash: 6042f651b2c148931d758afcbeab91ec74c5424ff2926c605ce939088a25c9b7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11857.22
# best_prompt_performance: 11849.24
# best_rel_error_pct: 0.067301
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_103228.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.1646241573203  # OPT_PARAM: {"initial": 420.1646241573203, "min": 350, "max": 500, "type": "float"}
    safety_stock = 60.16462415732091  # OPT_PARAM: {"initial": 60.16462415732091, "min": 40, "max": 90, "type": "float"}
    demand_estimate = 135.003568901896  # OPT_PARAM: {"initial": 135.003568901896, "min": 110, "max": 160, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.25, "type": "float"}
    recent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.1, "max": 0.6, "type": "float"}
    min_order_factor = 0.3091641845646975  # OPT_PARAM: {"initial": 0.3091641845646975, "min": 0.3, "max": 0.8, "type": "float"}
    max_order_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline components
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals

    # Dynamic adjustments with smoothing
    pipeline_adjustment = pipeline_weight * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Calculate target inventory position with smoothing
    target_position = (base_stock + safety_stock - pipeline_adjustment +
                      recent_adjustment * smoothing_factor)

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order (more conservative)
    min_order = max(0, min_order_factor * demand_estimate)
    order_amount = max(order_amount, min_order)

    # Apply maximum order limit based on demand estimate
    max_order = max_order_factor * demand_estimate
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
