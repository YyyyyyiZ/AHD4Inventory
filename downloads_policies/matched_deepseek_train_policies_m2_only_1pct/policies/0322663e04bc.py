# policy_hash: 0322663e04bca8dbc455224f176862bdf4f357cfdd7abfe473a9d942029f0932
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 3524.24
# best_prompt_performance: 3524.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_004253.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 428.4157620551528  # OPT_PARAM: {"initial": 428.4157620551528, "min": 350, "max": 500, "type": "float"}
    safety_stock = 108.41576205513881  # OPT_PARAM: {"initial": 108.41576205513881, "min": 60, "max": 140, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with tighter bounds
    max_order = 97.59146196184425  # OPT_PARAM: {"initial": 97.59146196184425, "min": 90, "max": 180, "type": "float"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 30, "type": "float"}

    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order and order_amount > 0:
        order_amount = min_order

    # Add demand anticipation based on recent pipeline orders
    recent_demand_estimate = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else 0
    demand_adjustment = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Adjust order based on demand pattern
    if inventory_position < target_inventory * 0.8:  # OPT_PARAM: {"initial": 0.8, "min": 0.6, "max": 0.9, "type": "float"}
        order_amount = min(max_order, order_amount + demand_adjustment)

    return order_amount
