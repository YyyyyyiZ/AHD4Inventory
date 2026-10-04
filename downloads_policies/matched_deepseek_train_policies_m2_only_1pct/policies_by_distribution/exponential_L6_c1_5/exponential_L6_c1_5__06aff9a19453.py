# policy_hash: 06aff9a194536b315d61d10dbb42ad78f6bea6a15578c7be0572aed57bbb1a36
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 12942.56
# best_prompt_performance: 12942.2
# best_rel_error_pct: 0.002782
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_100903.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.505328369579  # OPT_PARAM: {"initial": 420.505328369579, "min": 200, "max": 600, "type": "float"}
    safety_stock = 80.50532836957903  # OPT_PARAM: {"initial": 80.50532836957903, "min": 30, "max": 150, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 60, "max": 200, "type": "float"}
    pipeline_coverage = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    recent_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 0.7, "type": "float"}
    min_order_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals

    # Adjust target based on pipeline coverage
    # Higher pipeline_coverage means we rely more on incoming orders
    pipeline_adjustment = pipeline_coverage * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock - pipeline_adjustment + recent_adjustment

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order with smoother adjustment
    min_order = max(0, min_order_factor * demand_estimate - pipeline_orders[-1] if pipeline_orders else min_order_factor * demand_estimate)
    order_amount = max(order_amount, min_order)

    # Round to nearest integer (orders should be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
