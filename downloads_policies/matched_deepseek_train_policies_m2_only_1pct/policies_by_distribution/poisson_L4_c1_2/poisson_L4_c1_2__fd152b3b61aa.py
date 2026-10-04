# policy_hash: fd152b3b61aa799fd2acec955a454f725a3f0a52bbab973c6aadf3f24ffe4ed4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 809.88
# best_prompt_performance: 807.96
# best_rel_error_pct: 0.237072
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_080244.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 100.47080906847059  # OPT_PARAM: {"initial": 100.47080906847059, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 96.35134739695515  # OPT_PARAM: {"initial": 96.35134739695515, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.8, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = lead_time * demand_forecast

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_position as order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 1.5 * demand_forecast:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = raw_order

    # Round to nearest integer (orders must be integer quantities)
    return order_amount
