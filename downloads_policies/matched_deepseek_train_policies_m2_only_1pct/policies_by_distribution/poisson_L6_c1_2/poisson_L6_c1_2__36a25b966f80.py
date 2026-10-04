# policy_hash: 36a25b966f80b582d477b5f7b947701395e5e63fda0dd5e05b5e2c268518d17c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 46
# source_prompt_files: 1
# best_target_performance: 761.09
# best_prompt_performance: 761.09
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050956.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 697.2345718869553  # OPT_PARAM: {"initial": 697.2345718869553, "min": 400, "max": 800, "type": "float"}
    safety_stock = 95.74247987948092  # OPT_PARAM: {"initial": 95.74247987948092, "min": 50, "max": 150, "type": "float"}
    demand_estimate = 119.33415585030438  # OPT_PARAM: {"initial": 119.33415585030438, "min": 80, "max": 120, "type": "float"}
    max_order = 95.78759693603301  # OPT_PARAM: {"initial": 95.78759693603301, "min": 80, "max": 200, "type": "float"}
    min_order = 47.01206551001327  # OPT_PARAM: {"initial": 47.01206551001327, "min": 0, "max": 80, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

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
