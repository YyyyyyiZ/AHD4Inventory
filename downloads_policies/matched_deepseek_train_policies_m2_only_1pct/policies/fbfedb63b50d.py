# policy_hash: fbfedb63b50d4c74af83fca0a7492293a4e03ca30aa4853f5d3a46c307ffbd9a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 11567.96
# best_prompt_performance: 11568.18
# best_rel_error_pct: 0.001902
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_103354.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.503249041618  # OPT_PARAM: {"initial": 380.503249041618, "min": 300, "max": 450, "type": "float"}
    safety_factor = 1.3699097397586981  # OPT_PARAM: {"initial": 1.3699097397586981, "min": 1.2, "max": 1.6, "type": "float"}
    smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    lead_time = 6
    min_order = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

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

    # Apply minimum order quantity to avoid tiny orders
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order

    # Round to integer
    order_amount = int(round(order_amount))

    return order_amount
