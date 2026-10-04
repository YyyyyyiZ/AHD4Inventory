# policy_hash: 1c4bd8154996241040495217c6a998622a2b0e4343d323f5f31eb95d4e54be7a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 810.78
# best_prompt_performance: 810.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_051517.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 680.9812420911642  # OPT_PARAM: {"initial": 680.9812420911642, "min": 500, "max": 750, "type": "float"}
    safety_stock = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 160, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 90, "max": 110, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    min_order = 16.347799944421624  # OPT_PARAM: {"initial": 16.347799944421624, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_demand_during_leadtime = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply base stock level as upper bound
    if inventory_position + order_amount > base_stock:
        order_amount = max(0, base_stock - inventory_position)

    # Apply both upper and lower bounds
    order_amount = min(order_amount, max_order)
    order_amount = max(order_amount, min_order)

    return order_amount
