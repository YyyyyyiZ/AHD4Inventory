# policy_hash: 8d61ccd2cae78b3c7c359e2e0fa04ba5c476bb2445c17c43bc05752bafa0a90b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 738.98
# best_prompt_performance: 739.96
# best_rel_error_pct: 0.132615
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_082344.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 450, "max": 550, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 40, "max": 100, "type": "float"}
    demand_forecast = 95.79664347383132  # OPT_PARAM: {"initial": 95.79664347383132, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = (lead_time + 1) * demand_forecast

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Use base_stock as upper bound, target_position as lower bound
    order_up_to = min(base_stock, max(target_position, expected_lead_time_demand))

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
