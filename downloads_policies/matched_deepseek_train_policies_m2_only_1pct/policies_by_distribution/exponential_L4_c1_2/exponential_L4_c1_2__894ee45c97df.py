# policy_hash: 894ee45c97dfa7c7446638bbffaa32b5fd669f2375d866d590d2d5a54ef106a0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6160.4
# best_prompt_performance: 6160.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041309.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 187.80000000000527  # OPT_PARAM: {"initial": 187.80000000000527, "min": 100, "max": 300, "type": "float"}
    safety_stock = 57.80000000000472  # OPT_PARAM: {"initial": 57.80000000000472, "min": 20, "max": 100, "type": "float"}
    demand_forecast_factor = 1.0999999999999999  # OPT_PARAM: {"initial": 1.0999999999999999, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

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
