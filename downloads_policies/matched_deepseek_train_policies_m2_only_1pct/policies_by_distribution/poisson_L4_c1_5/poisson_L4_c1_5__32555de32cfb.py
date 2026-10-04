# policy_hash: 32555de32cfbf75f32b8bf90a533ef488daa068d5e5cf9059d533f971a414669
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2035.52
# best_prompt_performance: 2036.2
# best_rel_error_pct: 0.033407
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_045049.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 505.19989207384083  # OPT_PARAM: {"initial": 505.19989207384083, "min": 300, "max": 600, "type": "float"}
    safety_stock = 85.1998920738462  # OPT_PARAM: {"initial": 85.1998920738462, "min": 20, "max": 120, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

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
