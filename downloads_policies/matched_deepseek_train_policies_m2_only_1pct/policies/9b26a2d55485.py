# policy_hash: 9b26a2d55485391cbaf239b17ca45d778dbeecdee15fa91096b919786ed75f0b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 6254.42
# best_prompt_performance: 6254.42
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000243.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 305.1999999999899  # OPT_PARAM: {"initial": 305.1999999999899, "min": 100, "max": 500, "type": "float"}
    safety_stock = 38.99999999999636  # OPT_PARAM: {"initial": 38.99999999999636, "min": 0, "max": 100, "type": "float"}
    demand_smoothing = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using exponential smoothing of recent arrivals
    # Only use arrivals from the last 2 periods for more responsiveness
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]
        # Simple average of recent arrivals
        avg_recent_demand = sum(recent_arrivals) / 2
    else:
        # Conservative fallback
        avg_recent_demand = base_stock / 4

    # Adjust base stock based on recent demand trend
    # Use moderate adjustment to balance responsiveness and stability
    demand_adjustment = demand_smoothing * (avg_recent_demand - base_stock/4)
    adjusted_base_stock = base_stock + demand_adjustment

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to order amount
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
