# policy_hash: b38534d2a069245c8b3a307ed069d044b8a57fca66ca6d6a30aca72c2f9db14d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 2420.66
# best_prompt_performance: 2422.9
# best_rel_error_pct: 0.092537
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_070959.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 703.7720453536263  # OPT_PARAM: {"initial": 703.7720453536263, "min": 550, "max": 750, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 70, "max": 150, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.0, "type": "float"}
    smoothing_exponent = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_forecast_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.7, "max": 1.1, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic order-up-to level based on pipeline composition
    # Give more weight to near-term arrivals
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = 1.0 - (i / (len(pipeline_orders) * 2))  # Decreasing weight for farther orders
        weighted_pipeline += order * weight

    # Adjust base stock based on pipeline timing
    pipeline_timing_factor = 1.0 + (weighted_pipeline / (sum(pipeline_orders) + 1)) * 0.1

    # Calculate order-up-to level
    order_up_to = (base_stock * pipeline_timing_factor + safety_stock) * demand_forecast_factor

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if order_amount > 0:
        order_amount = order_amount ** smoothing_exponent

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
