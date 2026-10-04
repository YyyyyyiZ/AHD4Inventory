# policy_hash: 5163302b49f1706227072a78f5a7cd5e22b20979de39450a43d9fc0e4e161f58
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2113.38
# best_prompt_performance: 2112.78
# best_rel_error_pct: 0.028391
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044113.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0  # OPT_PARAM: {"initial": 520.0, "min": 400, "max": 650, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 60, "type": "float"}
    smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
