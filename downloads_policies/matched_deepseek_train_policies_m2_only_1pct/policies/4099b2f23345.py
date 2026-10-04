# policy_hash: 4099b2f233454aa9631b5e6b2d9bf7678442f4896e847b4f87ce772813dc091f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 42
# source_prompt_files: 1
# best_target_performance: 3525.36
# best_prompt_performance: 3525.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_003717.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 398.26889996445334  # OPT_PARAM: {"initial": 398.26889996445334, "min": 200, "max": 600, "type": "float"}
    safety_stock = 138.2688999644543  # OPT_PARAM: {"initial": 138.2688999644543, "min": 50, "max": 250, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with tighter bounds
    max_order = 97.56630065088954  # OPT_PARAM: {"initial": 97.56630065088954, "min": 50, "max": 300, "type": "float"}
    min_order = 25.085012377691207  # OPT_PARAM: {"initial": 25.085012377691207, "min": 0, "max": 100, "type": "float"}

    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order and order_amount > 0:
        order_amount = min_order

    return order_amount
