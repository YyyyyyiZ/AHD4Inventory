# policy_hash: 4feb8ad4141dd775beef29cdb5663cba8c96eca49127c7f9059bd30d6f54c04c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6164.66
# best_prompt_performance: 6164.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040627.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 215.93598745761454  # OPT_PARAM: {"initial": 215.93598745761454, "min": 100, "max": 400, "type": "float"}
    safety_stock = 75.93598745761456  # OPT_PARAM: {"initial": 75.93598745761456, "min": 30, "max": 150, "type": "float"}
    demand_forecast_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 1.5, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted average of pipeline orders for demand forecasting
    weighted_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** i
        weighted_pipeline += order * weight
        total_weight += weight

    avg_weighted_demand = weighted_pipeline / total_weight if total_weight > 0 else 0

    # Adjust base stock based on weighted demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_weighted_demand

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing using last order placed
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
