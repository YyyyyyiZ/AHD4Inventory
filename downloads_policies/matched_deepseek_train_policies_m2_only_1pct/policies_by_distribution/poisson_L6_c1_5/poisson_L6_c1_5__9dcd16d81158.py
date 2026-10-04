# policy_hash: 9dcd16d81158e9fa4094d0f4d4f171bf65cdbca5651a8dded447856861d2ba8b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3643.5
# best_prompt_performance: 3651.06
# best_rel_error_pct: 0.207493
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093126.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 697.9997381352779  # OPT_PARAM: {"initial": 697.9997381352779, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 150.00001261168097  # OPT_PARAM: {"initial": 150.00001261168097, "min": 0, "max": 300, "type": "float"}
    adjustment_factor = 0.32763588746307243  # OPT_PARAM: {"initial": 0.32763588746307243, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock adjustment
    target_inventory = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    raw_order = max(0, target_inventory - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
