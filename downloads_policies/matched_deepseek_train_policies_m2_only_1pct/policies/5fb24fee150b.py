# policy_hash: 5fb24fee150b3072d35f78b7e4eea26362f26bae7d19ff49bbd3b4896b80cb99
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1393.98
# best_prompt_performance: 1397.08
# best_rel_error_pct: 0.222385
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_011818.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0  # OPT_PARAM: {"initial": 520.0, "min": 400, "max": 700, "type": "float"}
    safety_stock = 55.0  # OPT_PARAM: {"initial": 55.0, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 98.0  # OPT_PARAM: {"initial": 98.0, "min": 90, "max": 110, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_demand_during_leadtime = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing
    smoothing_factor = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Cap order amount based on demand estimate
    max_order = demand_estimate * 1.15  # OPT_PARAM: {"initial": 1.15, "min": 1.0, "max": 2.0, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
