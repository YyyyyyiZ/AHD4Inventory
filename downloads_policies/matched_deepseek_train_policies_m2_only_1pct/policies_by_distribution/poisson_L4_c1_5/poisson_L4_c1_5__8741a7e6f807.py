# policy_hash: 8741a7e6f807c201eb8ae5b3c977fb076daa17f1a0c088ac801b1820117a5afa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2055.65
# best_prompt_performance: 2059.3
# best_rel_error_pct: 0.177559
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044930.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 510.76587478336717  # OPT_PARAM: {"initial": 510.76587478336717, "min": 300, "max": 700, "type": "float"}
    safety_stock = 55.765874783374  # OPT_PARAM: {"initial": 55.765874783374, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 1.0, "type": "float"}

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
