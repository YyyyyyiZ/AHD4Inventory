# policy_hash: db096342d8a35ce0ed9659d7ca71c4ee1ef5a73d43b707f4603c03032bb27739
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 2
# best_target_performance: 2186.4
# best_prompt_performance: 2186.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081635.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 505.0  # OPT_PARAM: {"initial": 505.0, "min": 400, "max": 600, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 20, "max": 100, "type": "float"}
    pipeline_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)
    target = base_stock + safety_stock * (1.0 - pipeline_factor)

    order_amount = max(0, target - inventory_position)

    # Smooth ordering adjustment
    if order_amount > 0:
        order_amount = int(round(order_amount))

    return order_amount
