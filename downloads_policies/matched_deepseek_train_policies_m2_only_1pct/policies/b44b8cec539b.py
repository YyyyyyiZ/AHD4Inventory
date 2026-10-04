# policy_hash: b44b8cec539bac3f789712dde9a8c481dd153c2ae9ef7e0099547e87a775e731
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1033.82
# best_prompt_performance: 1033.38
# best_rel_error_pct: 0.042561
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_184505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 109.17087461164785  # OPT_PARAM: {"initial": 109.17087461164785, "min": 50, "max": 200, "type": "float"}
    demand_estimate = 101.38376682973427  # OPT_PARAM: {"initial": 101.38376682973427, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply base stock as upper bound
    base_stock_order = max(0, base_stock - inventory_position)

    # Take the minimum of the two approaches
    order_amount = min(raw_order, base_stock_order)

    # Apply smoothing to reduce order volatility
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative and round to integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
