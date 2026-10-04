# policy_hash: 5cdc4e78412202d8224a79cf3a5bcf0389565beb4133b741183920d67c72b0d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3561.14
# best_prompt_performance: 3561.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045735.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 625.0  # OPT_PARAM: {"initial": 625.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 10, "max": 150, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 70, "max": 130, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = base_stock * 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 2.5, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
