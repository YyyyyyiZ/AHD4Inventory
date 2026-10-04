# policy_hash: 6c6cb423948b0ca9d7cf0de38ffae8adfe8536255f5c0b0008d207691139510b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 16
# source_prompt_files: 2
# best_target_performance: 10299.88
# best_prompt_performance: 10299.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231900.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.37538551968174  # OPT_PARAM: {"initial": 286.37538551968174, "min": 100, "max": 500, "type": "float"}
    safety_stock = 76.3753855196821  # OPT_PARAM: {"initial": 76.3753855196821, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.5857952564014022  # OPT_PARAM: {"initial": 0.5857952564014022, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple target calculation without complex pipeline weighting
    target = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Apply smoothing to avoid extreme orders
    if order_amount > 0:
        # Use simple exponential smoothing
        order_amount = smoothing_factor * order_amount

    # Round to integer (as required by problem statement)
    return order_amount
