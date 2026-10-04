# policy_hash: dab5e20ae89e1b58a65f2c26c73bbb4f23f7a2d3c3a80f310e04e11e10197cdb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 38
# source_prompt_files: 1
# best_target_performance: 3813.14
# best_prompt_performance: 3813.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_080426.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 984.953062156823  # OPT_PARAM: {"initial": 984.953062156823, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 284.9530621568182  # OPT_PARAM: {"initial": 284.9530621568182, "min": 0, "max": 300, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    desired_order = max(0, target_inventory - inventory_position)
    order_amount = smoothing_factor * desired_order

    # Round to nearest integer (since order amount should be integer)
    return order_amount
