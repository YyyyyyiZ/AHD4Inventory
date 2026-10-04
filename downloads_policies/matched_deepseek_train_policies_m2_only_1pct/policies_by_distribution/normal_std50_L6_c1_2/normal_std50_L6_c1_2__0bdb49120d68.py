# policy_hash: 0bdb49120d6862a166cb5ead7dac22826f4159bba53d3f9468fab0417fe57348
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4399.94
# best_prompt_performance: 4386.54
# best_rel_error_pct: 0.304550
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_231150.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 476.5819915422721  # OPT_PARAM: {"initial": 476.5819915422721, "min": 300, "max": 650, "type": "float"}
    safety_stock = 56.58199154227133  # OPT_PARAM: {"initial": 56.58199154227133, "min": 30, "max": 120, "type": "float"}
    smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.900000000001758  # OPT_PARAM: {"initial": 0.900000000001758, "min": 0.9, "max": 1.3, "type": "float"}
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

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with pipeline consideration
    if raw_order > 0:
        # Use recent pipeline orders for adjustment
        recent_pipeline = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
        if recent_pipeline and avg_pipeline > 0:
            recent_avg = sum(recent_pipeline) / len(recent_pipeline)
            pipeline_ratio = min(1.5, recent_avg / (avg_pipeline + 1e-6))
            adjustment = 1.0 - pipeline_weight * (1.0 - min(1.0, pipeline_ratio))
            effective_smoothing = min(1.0, smoothing_factor * adjustment)
        else:
            effective_smoothing = smoothing_factor
    else:
        effective_smoothing = 1.0

    order_amount = max(0, effective_smoothing * raw_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
