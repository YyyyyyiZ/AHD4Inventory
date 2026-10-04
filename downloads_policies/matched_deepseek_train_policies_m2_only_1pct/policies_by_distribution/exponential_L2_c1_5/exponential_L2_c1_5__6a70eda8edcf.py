# policy_hash: 6a70eda8edcff8b7250bb6dbc450fcf6f202db58d457a7d6c6cf4c5968829ee1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 10205.76
# best_prompt_performance: 10205.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231851.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 351.0970750349791  # OPT_PARAM: {"initial": 351.0970750349791, "min": 100, "max": 600, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 0, "max": 150, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 50, "max": 300, "type": "float"}
    pipeline_factor = 0.6318791141181664  # OPT_PARAM: {"initial": 0.6318791141181664, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing = 0.458912150502515  # OPT_PARAM: {"initial": 0.458912150502515, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    if len(pipeline_orders) > 0:
        pipeline_coverage = sum(pipeline_orders) * pipeline_factor
    else:
        pipeline_coverage = 0

    # Adjust base stock based on pipeline coverage
    adjusted_base = base_stock - pipeline_coverage

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, demand_estimate + safety_stock)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    if raw_order > 0 and len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing * raw_order + (1 - smoothing) * avg_pipeline
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    return order_amount
