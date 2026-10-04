# policy_hash: b67a1c3bf189c65bb82a40bcaf68144881808d090e85df08d82ef378a1f169c9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 1341.14
# best_prompt_performance: 1341.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230317.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.9814814814807  # OPT_PARAM: {"initial": 308.9814814814807, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply base stock as upper bound
    base_stock_order = max(0, base_stock - inventory_position)
    order_amount = min(order_amount, base_stock_order)

    return order_amount
