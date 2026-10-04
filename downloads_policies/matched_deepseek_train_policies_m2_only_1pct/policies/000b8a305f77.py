# policy_hash: 000b8a305f77b386d82eb066d07fb1fb115090c75529bec14ac83491765e3c8b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 4133.46
# best_prompt_performance: 4134.14
# best_rel_error_pct: 0.016451
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_015844.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 535.5027417865231  # OPT_PARAM: {"initial": 535.5027417865231, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 78.5462756209894  # OPT_PARAM: {"initial": 78.5462756209894, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.3972517939956193  # OPT_PARAM: {"initial": 0.3972517939956193, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order-up-to level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_level - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        order_amount = int(round(smoothing_factor * raw_order))
    else:
        order_amount = 0

    return order_amount
