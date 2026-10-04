# policy_hash: 90e6216aae30aa13aade7cad49a61e1bf6ab2647ad3b66388bdc034aed049400
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 810.79
# best_prompt_performance: 810.79
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_200644.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.21155119005713  # OPT_PARAM: {"initial": 58.21155119005713, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 124.55298284918987  # OPT_PARAM: {"initial": 124.55298284918987, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap the order amount to avoid excessive ordering
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
