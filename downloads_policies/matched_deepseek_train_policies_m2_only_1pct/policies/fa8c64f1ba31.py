# policy_hash: fa8c64f1ba311ee2fd7cd3061253da39cc960bf8391661dc6b3d184b982fc1a1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2890.36
# best_prompt_performance: 2876.88
# best_rel_error_pct: 0.466378
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_021748.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 90.46709878120107  # OPT_PARAM: {"initial": 90.46709878120107, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 114.69539833812935  # OPT_PARAM: {"initial": 114.69539833812935, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap the order amount to avoid excessive ordering
    max_order = base_stock - inventory_position + demand_estimate
    order_amount = min(order_amount, max(0, max_order))

    return order_amount
