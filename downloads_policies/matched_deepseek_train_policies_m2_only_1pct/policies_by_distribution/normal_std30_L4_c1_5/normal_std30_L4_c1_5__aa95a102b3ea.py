# policy_hash: aa95a102b3ea9c43bd4ddad55a9553950350d05f8199783ac8fc52be8b567005
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 3524.23
# best_prompt_performance: 3524.23
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_004647.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 418.99191617032926  # OPT_PARAM: {"initial": 418.99191617032926, "min": 300, "max": 450, "type": "float"}
    safety_stock = 117.94905348537525  # OPT_PARAM: {"initial": 117.94905348537525, "min": 50, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with tighter bounds
    max_order = 97.59798068792418  # OPT_PARAM: {"initial": 97.59798068792418, "min": 80, "max": 160, "type": "float"}
    min_order = 6.765480219413178  # OPT_PARAM: {"initial": 6.765480219413178, "min": 0, "max": 20, "type": "float"}

    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order and order_amount > 0:
        order_amount = min_order

    # Add demand anticipation based on recent pipeline orders
    recent_demand_estimate = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else 0
    demand_adjustment = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.4, "type": "float"}

    # Adjust order based on inventory position relative to target
    if inventory_position < target_inventory * 0.7:  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.85, "type": "float"}
        order_amount = min(max_order, order_amount + demand_adjustment * recent_demand_estimate)

    return order_amount
