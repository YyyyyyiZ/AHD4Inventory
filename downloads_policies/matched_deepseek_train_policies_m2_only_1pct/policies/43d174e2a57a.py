# policy_hash: 43d174e2a57a4ebf86241a46a96efaeb97fc7e09cbc3ef60baa6ae0d10984d4b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1256.38
# best_prompt_performance: 1254.56
# best_rel_error_pct: 0.144861
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005721.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 415.60815534383784  # OPT_PARAM: {"initial": 415.60815534383784, "min": 400, "max": 500, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.00636940359931  # OPT_PARAM: {"initial": 95.00636940359931, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5948840012436081  # OPT_PARAM: {"initial": 0.5948840012436081, "min": 0.5, "max": 1.0, "type": "float"}
    min_coverage = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.7, "max": 1.2, "type": "float"}

    # Calculate total pipeline inventory
    total_pipeline = sum(pipeline_orders)
    weighted_pipeline = pipeline_weight * total_pipeline

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Simple order-up-to level without complex pipeline adjustments
    order_up_to = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure minimum coverage of forecasted demand
    immediate_arrival = pipeline_orders[0] if pipeline_orders else 0
    min_order = max(0, demand_forecast * min_coverage - immediate_arrival)
    final_order = max(min_order, smoothed_order)

    # Round to nearest integer
    order_amount = max(0, int(round(final_order)))

    return order_amount
