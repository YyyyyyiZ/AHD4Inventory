# policy_hash: a01ded7434c0e1f2bc067fd88fa23fa95d04b12f3ec39aeea0631cd9735e8f08
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1094.88
# best_prompt_performance: 1095.28
# best_rel_error_pct: 0.036534
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074634.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 423.8458935903485  # OPT_PARAM: {"initial": 423.8458935903485, "min": 350, "max": 500, "type": "float"}
    safety_stock = 33.845893590350386  # OPT_PARAM: {"initial": 33.845893590350386, "min": 10, "max": 40, "type": "float"}
    pipeline_weight = 0.9579277465887924  # OPT_PARAM: {"initial": 0.9579277465887924, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing using last order as reference
    last_order = pipeline_orders[-1] if pipeline_orders else 0
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
