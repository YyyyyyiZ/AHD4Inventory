# policy_hash: 0498aeee745890841a78e49951cb4e7ad0f560b912b6c98743a4b6aee7eb54a4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 985.7
# best_prompt_performance: 985.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_022257.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 340.0  # OPT_PARAM: {"initial": 340.0, "min": 250, "max": 450, "type": "float"}
    safety_stock = 166.1539418660919  # OPT_PARAM: {"initial": 166.1539418660919, "min": 80, "max": 220, "type": "float"}
    demand_estimate = 108.65394186609191  # OPT_PARAM: {"initial": 108.65394186609191, "min": 80, "max": 130, "type": "float"}
    lead_time_demand_factor = 1.2957103323109969  # OPT_PARAM: {"initial": 1.2957103323109969, "min": 0.9, "max": 1.3, "type": "float"}
    smoothing_factor = 0.8794193598693082  # OPT_PARAM: {"initial": 0.8794193598693082, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with adjustment factor
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders) * lead_time_demand_factor

    # Calculate target inventory level
    target_inventory = expected_demand_during_leadtime + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - net_inventory)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * raw_order

    # Apply base stock as upper bound
    if net_inventory < base_stock:
        max_order = base_stock - net_inventory
        smoothed_order = min(smoothed_order, max_order)
    else:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
