# policy_hash: 06bcd152f99b365dbadc875b7c40989433287d62635e12ddf7c262f4d9b02cba
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 3207.8
# best_prompt_performance: 3207.48
# best_rel_error_pct: 0.009976
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_163444.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 649.9968150494108  # OPT_PARAM: {"initial": 649.9968150494108, "min": 400, "max": 900, "type": "float"}
    safety_stock = 80.09681504941081  # OPT_PARAM: {"initial": 80.09681504941081, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.6992037623527038  # OPT_PARAM: {"initial": 0.6992037623527038, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    order_amount = int(round(smoothing_factor * raw_order))

    return order_amount
