# policy_hash: 803d4a8c77b3bd51c970e08ea87f9f03de4f3b752f334fdba19343e7867b805b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 765.09
# best_prompt_performance: 765.08
# best_rel_error_pct: 0.001307
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_201340.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 80, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap the order amount
    max_order = 95.91650931968574  # OPT_PARAM: {"initial": 95.91650931968574, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Add minimum order quantity
    min_order = 10.250595622612082  # OPT_PARAM: {"initial": 10.250595622612082, "min": 0, "max": 30, "type": "float"}
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer as required
    return order_amount
