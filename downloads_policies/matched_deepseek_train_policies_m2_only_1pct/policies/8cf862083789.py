# policy_hash: 8cf862083789ba36c842c22757b876dcd36f5dac446d5ec662ea27d6425302ae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 3524.25
# best_prompt_performance: 3524.25
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_003826.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 432.1862961269562  # OPT_PARAM: {"initial": 432.1862961269562, "min": 300, "max": 550, "type": "float"}
    safety_stock = 104.41441046391277  # OPT_PARAM: {"initial": 104.41441046391277, "min": 80, "max": 180, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with tighter bounds
    max_order = 97.56171074763496  # OPT_PARAM: {"initial": 97.56171074763496, "min": 80, "max": 250, "type": "float"}
    min_order = 14.37813437426234  # OPT_PARAM: {"initial": 14.37813437426234, "min": 0, "max": 50, "type": "float"}

    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order and order_amount > 0:
        order_amount = min_order

    return order_amount
