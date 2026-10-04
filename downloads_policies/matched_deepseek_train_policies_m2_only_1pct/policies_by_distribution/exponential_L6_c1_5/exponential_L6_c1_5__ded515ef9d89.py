# policy_hash: ded515ef9d895ca213e813c66bcc26a681343aaf918542b8ff8b88989f21c412
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 12722.86
# best_prompt_performance: 12722.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101029.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 438.9025941224495  # OPT_PARAM: {"initial": 438.9025941224495, "min": 200, "max": 600, "type": "float"}
    safety_stock = 59.00259412245358  # OPT_PARAM: {"initial": 59.00259412245358, "min": 10, "max": 100, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 70, "max": 200, "type": "float"}
    pipeline_coverage = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    recent_weight = 0.7649862334707367  # OPT_PARAM: {"initial": 0.7649862334707367, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_factor = 0.3839365783546324  # OPT_PARAM: {"initial": 0.3839365783546324, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals

    # Adjust target based on pipeline coverage
    pipeline_adjustment = pipeline_coverage * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock - pipeline_adjustment + recent_adjustment

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order with smoothing
    min_order = min_order_factor * demand_estimate
    if order_amount < min_order:
        # Smooth transition to minimum order
        order_amount = max(order_amount, min_order)

    # Round to nearest integer (order quantities are integers)
    order_amount = int(round(order_amount))

    return order_amount
