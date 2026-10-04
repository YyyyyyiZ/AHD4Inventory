# policy_hash: e568c5fe16b5134139b42676da2d3750b8695d6acfb6e6099a29b365fe1c9a91
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3241.0
# best_prompt_performance: 3226.21
# best_rel_error_pct: 0.456341
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_002135.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 688.8163228555375  # OPT_PARAM: {"initial": 688.8163228555375, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 45.91605045591151  # OPT_PARAM: {"initial": 45.91605045591151, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.6578780704940559  # OPT_PARAM: {"initial": 0.6578780704940559, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position with safety stock
    target_inventory = base_stock + safety_stock

    # Smooth adjustment to avoid large order swings
    order_amount = max(0, smoothing_factor * (target_inventory - inventory_position))

    # Round to nearest integer for practical ordering
    return order_amount
