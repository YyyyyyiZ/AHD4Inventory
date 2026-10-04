# policy_hash: e667322ab9ffd8ea23d0c201aa06769463f227fe35f2dd43b57aece1113914aa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1609.34
# best_prompt_performance: 1615.76
# best_rel_error_pct: 0.398921
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_051011.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 52.73151749212548  # OPT_PARAM: {"initial": 52.73151749212548, "min": 20, "max": 120, "type": "float"}
    demand_estimate = 102.27431905951568  # OPT_PARAM: {"initial": 102.27431905951568, "min": 90, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_demand_during_leadtime = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position with dynamic adjustment
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing to avoid large order swings
    smoothing_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
    if order_amount > demand_estimate * 1.5:
        order_amount = demand_estimate * 1.5 + (order_amount - demand_estimate * 1.5) * smoothing_factor

    # Cap the order amount based on demand forecast
    max_order = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 100, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Minimum order threshold to avoid tiny orders
    min_order = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 0, "max": 50, "type": "float"}
    if 0 < order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))

    return order_amount
