# policy_hash: 4db26f66b16b21b73f8930bf76f9af354fb435282061a39d488e3c8fcf9ee785
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1621.93
# best_prompt_performance: 1621.93
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034558.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 457.04347743831954  # OPT_PARAM: {"initial": 457.04347743831954, "min": 300, "max": 600, "type": "float"}
    safety_stock = 57.14347743832106  # OPT_PARAM: {"initial": 57.14347743832106, "min": 0, "max": 150, "type": "float"}
    smoothing_factor = 0.6877282537595476  # OPT_PARAM: {"initial": 0.6877282537595476, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order-up-to level with safety stock
    desired_level = base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    order_amount = max(0, smoothing_factor * (desired_level - inventory_position))

    # Round to nearest integer for practical ordering
    return order_amount
