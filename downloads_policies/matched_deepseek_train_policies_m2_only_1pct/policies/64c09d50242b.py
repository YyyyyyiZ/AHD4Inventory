# policy_hash: 64c09d50242b7a44ad936dfdd8806b591a1d91d1af9fabdeaadf34f3b542a9c7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1271.46
# best_prompt_performance: 1269.92
# best_rel_error_pct: 0.121121
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005040.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.60987510851004  # OPT_PARAM: {"initial": 420.60987510851004, "min": 400, "max": 500, "type": "float"}
    safety_stock = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 10, "max": 40, "type": "float"}
    demand_forecast = 95.00791422951629  # OPT_PARAM: {"initial": 95.00791422951629, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5940695228244032  # OPT_PARAM: {"initial": 0.5940695228244032, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate total pipeline with weighted future arrivals
    total_pipeline = sum(pipeline_orders)
    weighted_pipeline = pipeline_weight * total_pipeline

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    immediate_arrival = pipeline_orders[0] if pipeline_orders else 0
    near_term_pipeline = sum(pipeline_orders[1:3]) if len(pipeline_orders) > 2 else 0

    # Adjust base stock based on pipeline distribution
    if immediate_arrival < demand_forecast * 0.7 and near_term_pipeline < demand_forecast * 1.5:
        adjusted_base = base_stock * 1.05
    else:
        adjusted_base = base_stock

    order_up_to = adjusted_base + safety_stock

    # Calculate order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order covers at least one period of demand
    min_order = max(0, demand_forecast * 0.8 - immediate_arrival)
    final_order = max(min_order, smoothed_order)

    # Round to nearest integer
    order_amount = max(0, int(round(final_order)))

    return order_amount
