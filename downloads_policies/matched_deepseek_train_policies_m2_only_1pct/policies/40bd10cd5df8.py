# policy_hash: 40bd10cd5df8a032bf695637d6a160d81d43a356dd22a388426d6c15cc1f858c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 4198.88
# best_prompt_performance: 4195.56
# best_rel_error_pct: 0.079069
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230626.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 452.11423949027153  # OPT_PARAM: {"initial": 452.11423949027153, "min": 200, "max": 700, "type": "float"}
    safety_stock = 82.11423949027319  # OPT_PARAM: {"initial": 82.11423949027319, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_forecast_factor = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 0.8, "max": 1.3, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate average pipeline order as demand indicator
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
    else:
        avg_pipeline = 0

    # Forecast demand using pipeline average with adjustment factor
    forecast_demand = demand_forecast_factor * avg_pipeline

    # Adjust base stock based on forecast
    adjusted_base_stock = base_stock + forecast_demand

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate order quantity with smoothing
    raw_order = max(0, order_up_to - inventory_position)

    # Apply pipeline-aware smoothing: more aggressive when pipeline is low
    if avg_pipeline > 0 and raw_order > 0:
        pipeline_ratio = min(1.0, sum(pipeline_orders[:3]) / (3 * avg_pipeline + 1e-6))
        effective_smoothing = smoothing_factor * (1.0 - pipeline_weight * (1.0 - pipeline_ratio))
    else:
        effective_smoothing = smoothing_factor

    order_amount = max(0, effective_smoothing * raw_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
