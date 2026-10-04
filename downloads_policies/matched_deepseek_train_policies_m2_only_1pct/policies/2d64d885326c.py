# policy_hash: 2d64d885326c9fa5bb9e74da5bccbd1031cb5bbae6937111a564f79530881b58
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2181.62
# best_prompt_performance: 2180.4
# best_rel_error_pct: 0.055922
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_043201.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 461.5032175280156  # OPT_PARAM: {"initial": 461.5032175280156, "min": 300, "max": 600, "type": "float"}
    safety_stock = 51.50321752801812  # OPT_PARAM: {"initial": 51.50321752801812, "min": 20, "max": 80, "type": "float"}
    demand_estimate = 98.5  # OPT_PARAM: {"initial": 98.5, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    target_position = base_stock + safety_stock

    # Smooth order calculation to avoid over-reaction
    desired_order = max(0, target_position - inventory_position)

    # Blend with demand anticipation
    demand_based_order = max(0, expected_lead_time_demand - inventory_position)

    # Use weighted combination
    order_amount = smoothing_factor * desired_order + (1 - smoothing_factor) * demand_based_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
