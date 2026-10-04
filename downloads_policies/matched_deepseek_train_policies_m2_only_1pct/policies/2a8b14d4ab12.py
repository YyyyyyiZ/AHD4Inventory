# policy_hash: 2a8b14d4ab12e0ea5cb38f8724656c71de546f7a6662ec40bf1ec0303565019d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 11566.08
# best_prompt_performance: 11565.34
# best_rel_error_pct: 0.006398
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_102828.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 425.1198364658777  # OPT_PARAM: {"initial": 425.1198364658777, "min": 300, "max": 550, "type": "float"}
    safety_factor = 1.211747585825949  # OPT_PARAM: {"initial": 1.211747585825949, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory with safety factor
    target_inventory = base_stock * safety_factor

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply exponential smoothing to reduce order volatility
    if pipeline_orders:
        # Use average of last 3 orders for smoothing reference
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        avg_recent = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing * order_amount + (1 - smoothing) * avg_recent
        order_amount = max(0, smoothed_order)

    # Round to integer
    order_amount = int(round(order_amount))

    return order_amount
