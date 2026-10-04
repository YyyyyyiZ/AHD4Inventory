# policy_hash: 15eae5fc3d5b6e7c1ca6bcecab46ea1f39f8d7f22ed5cb3590c24fcb4e2b0659
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 11897.43
# best_prompt_performance: 11897.23
# best_rel_error_pct: 0.001681
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084157.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 430.87917335727207  # OPT_PARAM: {"initial": 430.87917335727207, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 50, "max": 400, "type": "float"}
    demand_forecast_factor = 0.18362628150983032  # OPT_PARAM: {"initial": 0.18362628150983032, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of recent pipeline orders as demand estimate
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[:2]  # Oldest orders represent recent demand fulfillment
        demand_estimate = sum(recent_orders) / len(recent_orders)
    else:
        demand_estimate = 0

    # Adjust base stock level based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * demand_estimate

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering by limiting maximum order size
    max_order = 278.5819995119752  # OPT_PARAM: {"initial": 278.5819995119752, "min": 100, "max": 600, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
