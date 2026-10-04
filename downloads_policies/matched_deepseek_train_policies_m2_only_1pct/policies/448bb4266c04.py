# policy_hash: 448bb4266c0493bbb68808b0d36c11e9575c4edadb9fca489ab63d26f7a903bb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 23
# source_prompt_files: 2
# best_target_performance: 857.12
# best_prompt_performance: 857.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075007.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.35515133433427  # OPT_PARAM: {"initial": 420.35515133433427, "min": 350, "max": 500, "type": "float"}
    safety_stock = 36.61507433427066  # OPT_PARAM: {"initial": 36.61507433427066, "min": 10, "max": 40, "type": "float"}
    pipeline_weight = 0.9801115696671294  # OPT_PARAM: {"initial": 0.9801115696671294, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    demand_forecast_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Calculate expected demand based on pipeline arrivals
    expected_demand = 100.0 * demand_forecast_factor  # Historical average demand ~100

    # Dynamic order-up-to level with demand adjustment
    order_up_to = base_stock + safety_stock + expected_demand * 0.1

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing using last order as reference
    last_order = pipeline_orders[-1] if pipeline_orders else 0
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order

    # Ensure order is at least expected demand minus current pipeline arrivals
    min_order = max(0, expected_demand - pipeline_orders[0] if pipeline_orders else expected_demand)
    smoothed_order = max(smoothed_order, min_order)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
