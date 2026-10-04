# policy_hash: 98b37415308778a05fdf0f62b9003a1c550f613f3e09ab5a366b4e711caac7a5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1103.01
# best_prompt_performance: 1103.01
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_184105.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 486.8812208497333  # OPT_PARAM: {"initial": 486.8812208497333, "min": 300, "max": 600, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 10, "max": 150, "type": "float"}
    demand_estimate = 110.66663300822742  # OPT_PARAM: {"initial": 110.66663300822742, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with smoothing
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount with smoothing to reduce volatility
    raw_order = max(0, target_position - inventory_position)

    # Apply base stock as upper bound with smoothing
    base_stock_order = max(0, base_stock - inventory_position)

    # Smooth the order amount to avoid large swings
    order_amount = min(raw_order, base_stock_order)
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * min(order_amount, demand_estimate)

    # Round to nearest integer (as required by output type)
    return order_amount
