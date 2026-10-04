# policy_hash: 14f39cfc2a8ed8e9324bbdf6af7e6032fc0c881e03bac76d57ee157e03b34072
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2509.4
# best_prompt_performance: 2509.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002700.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.90576867931185  # OPT_PARAM: {"initial": 449.90576867931185, "min": 300, "max": 700, "type": "float"}
    safety_stock = 59.528089111384126  # OPT_PARAM: {"initial": 59.528089111384126, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    order_amount = int(round(smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1] if pipeline_orders else raw_order))

    return order_amount
