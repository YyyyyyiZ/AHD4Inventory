# policy_hash: 1aa1e85d32a1d38d87623d2886a003c4b49dc6a1856e8be4fd191bf5a7bd51ed
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 760.86
# best_prompt_performance: 760.9
# best_rel_error_pct: 0.005257
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_010601.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.68920289431031  # OPT_PARAM: {"initial": 58.68920289431031, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 125.95458012559253  # OPT_PARAM: {"initial": 125.95458012559253, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 95.92075836356183  # OPT_PARAM: {"initial": 95.92075836356183, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
