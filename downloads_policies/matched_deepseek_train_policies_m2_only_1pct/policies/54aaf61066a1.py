# policy_hash: 54aaf61066a156801dedc5be641f2c3dd9b7a633f4949f7a56d22a0b956986f3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 37
# source_prompt_files: 1
# best_target_performance: 1349.8
# best_prompt_performance: 1349.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070043.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.306250464445  # OPT_PARAM: {"initial": 310.306250464445, "min": 250, "max": 350, "type": "float"}
    safety_stock = 38.64050595563791  # OPT_PARAM: {"initial": 38.64050595563791, "min": 10, "max": 50, "type": "float"}
    adjustment_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    raw_order = max(0, target_inventory - inventory_position)
    adjusted_order = raw_order * adjustment_factor

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
