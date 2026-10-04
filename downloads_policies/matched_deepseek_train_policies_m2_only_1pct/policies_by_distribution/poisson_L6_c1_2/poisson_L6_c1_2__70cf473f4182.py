# policy_hash: 70cf473f4182930924509219e7ec47cae0d90896db38d4c27d20d42c9fa40562
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 784.2
# best_prompt_performance: 784.37
# best_rel_error_pct: 0.021678
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052637.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 679.4438157456239  # OPT_PARAM: {"initial": 679.4438157456239, "min": 650, "max": 720, "type": "float"}
    safety_stock = 101.703479823355  # OPT_PARAM: {"initial": 101.703479823355, "min": 80, "max": 110, "type": "float"}
    demand_estimate = 102.03632316934876  # OPT_PARAM: {"initial": 102.03632316934876, "min": 95, "max": 105, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 140, "type": "float"}
    min_order = 5.2525398704876105  # OPT_PARAM: {"initial": 5.2525398704876105, "min": 0, "max": 10, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Simplified target calculation
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate base order
    raw_order = target_position - inventory_position
    order_amount = max(0, raw_order)

    # Apply smoothing
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Apply base stock constraint
    if inventory_position + order_amount > base_stock:
        order_amount = max(0, base_stock - inventory_position)

    # Apply practical bounds
    order_amount = min(order_amount, max_order)
    order_amount = max(order_amount, min_order)

    return order_amount
