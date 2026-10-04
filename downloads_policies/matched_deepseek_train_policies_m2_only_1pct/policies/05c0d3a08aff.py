# policy_hash: 05c0d3a08aff45f1e2b0bf5f8dfd01f01f89406f6ebd9f1cf612c39ab7925504
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11818.08
# best_prompt_performance: 11818.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_102606.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 385.20000000008974  # OPT_PARAM: {"initial": 385.20000000008974, "min": 300, "max": 450, "type": "float"}
    safety_stock = 45.20000000008979  # OPT_PARAM: {"initial": 45.20000000008979, "min": 30, "max": 70, "type": "float"}
    demand_estimate = 125.0  # OPT_PARAM: {"initial": 125.0, "min": 100, "max": 150, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.3, "type": "float"}
    recent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.2, "max": 0.6, "type": "float"}
    min_order_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.4, "max": 0.8, "type": "float"}
    max_order_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline components
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals

    # Dynamic adjustments
    pipeline_adjustment = pipeline_weight * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock - pipeline_adjustment + recent_adjustment

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order
    min_order = max(0, min_order_factor * demand_estimate - pipeline_orders[-1] if pipeline_orders else min_order_factor * demand_estimate)
    order_amount = max(order_amount, min_order)

    # Apply maximum order limit based on demand estimate
    max_order = max_order_factor * demand_estimate
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
