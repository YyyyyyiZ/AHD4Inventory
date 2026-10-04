# policy_hash: 5851880cf23f63c07c698db256b07521678a0578ca016417a4c4dc5d245699cc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 2555.86
# best_prompt_performance: 2556.34
# best_rel_error_pct: 0.018780
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_010544.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9045672215498  # OPT_PARAM: {"initial": 663.9045672215498, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.91501798339546  # OPT_PARAM: {"initial": 49.91501798339546, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.556732130894163  # OPT_PARAM: {"initial": 0.556732130894163, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position with safety stock
    target_position = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_position - inventory_position) * adjustment_factor)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
