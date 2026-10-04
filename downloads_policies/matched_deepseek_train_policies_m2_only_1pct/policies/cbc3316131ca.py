# policy_hash: cbc3316131cac98934d38561d78a2bb1774c0e0d7d69bfa0c16f14c91781a0d3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 744.21
# best_prompt_performance: 744.33
# best_rel_error_pct: 0.016124
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_080513.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 422.7427630434316  # OPT_PARAM: {"initial": 422.7427630434316, "min": 350, "max": 500, "type": "float"}
    safety_stock = 85.0  # OPT_PARAM: {"initial": 85.0, "min": 50, "max": 120, "type": "float"}
    demand_forecast = 95.30202471204655  # OPT_PARAM: {"initial": 95.30202471204655, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_lead_time_demand = (lead_time + 1) * demand_forecast

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Use the minimum of base_stock and target_position to balance costs
    order_up_to = min(base_stock, target_position)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing more consistently
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
