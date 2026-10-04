# policy_hash: a509ec3ac50aeda9ddcf77d01e94629a6c9e5f52771d40009152947b617107c9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 11633.84
# best_prompt_performance: 11633.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_061555.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 471.577983757099  # OPT_PARAM: {"initial": 471.577983757099, "min": 300, "max": 700, "type": "float"}
    safety_stock = 166.57798375709532  # OPT_PARAM: {"initial": 166.57798375709532, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.7217817465558706  # OPT_PARAM: {"initial": 0.7217817465558706, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
