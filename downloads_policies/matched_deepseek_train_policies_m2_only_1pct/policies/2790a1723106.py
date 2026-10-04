# policy_hash: 2790a1723106ef53e7036af65cf6da73f1e8875298cbff15721c6c1ee2411aac
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1569.44
# best_prompt_performance: 1574.8
# best_rel_error_pct: 0.341523
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050635.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 300, "max": 700, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    min_order = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 10, "max": 100, "type": "float"}
    safety_stock_multiplier = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Add safety stock based on lead time variability
    safety_stock = safety_stock_multiplier * demand_forecast * (lead_time ** 0.5)

    # Calculate target inventory position
    target_inventory_position = base_stock + expected_demand_during_lead_time + safety_stock

    # Calculate order amount with exponential smoothing
    raw_order = max(0, target_inventory_position - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure minimum order quantity
    order_amount = max(min_order, smoothed_order)

    return order_amount
