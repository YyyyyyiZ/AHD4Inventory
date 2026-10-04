# policy_hash: 9b273d65dac18b17da300620d0b25e666fbb7490b937f85a247a46a62538dd44
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2148.26
# best_prompt_performance: 2156.14
# best_rel_error_pct: 0.366808
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_042425.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.999507244149  # OPT_PARAM: {"initial": 449.999507244149, "min": 300, "max": 600, "type": "float"}
    safety_stock = 59.99950724414902  # OPT_PARAM: {"initial": 59.99950724414902, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.9587114323135197  # OPT_PARAM: {"initial": 0.9587114323135197, "min": 0.5, "max": 1.0, "type": "float"}

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
