# policy_hash: 0071d5a633f53cc1895f3a8721a44d9ac2b5b239a6066a9c14b5babc0e62182a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10279.66
# best_prompt_performance: 10279.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033316.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 285.4  # OPT_PARAM: {"initial": 285.4, "min": 150, "max": 400, "type": "float"}
    safety_stock = 38.7  # OPT_PARAM: {"initial": 38.7, "min": 15, "max": 80, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate basic order-up-to amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with dynamic bounds
    max_order = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 120, "max": 350, "type": "float"}
    min_order = 18.2  # OPT_PARAM: {"initial": 18.2, "min": 5, "max": 40, "type": "float"}

    # Dynamic adjustment based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (base_stock + 1e-6)
    if pipeline_ratio > 0.6:
        max_order = max_order * 0.85
    elif pipeline_ratio < 0.3:
        min_order = min_order * 1.2

    # Cap the order amount
    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order and order_amount > 0:
        order_amount = min_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
