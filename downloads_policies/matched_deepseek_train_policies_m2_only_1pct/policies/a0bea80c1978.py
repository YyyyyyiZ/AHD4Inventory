# policy_hash: a0bea80c19785fd87368b79f32963488b9258bd04dbea0ca99ebcc797786ba4d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 39
# source_prompt_files: 3
# best_target_performance: 11292.32
# best_prompt_performance: 11292.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005712.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 410.1604576694377  # OPT_PARAM: {"initial": 410.1604576694377, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.1  # OPT_PARAM: {"initial": 50.1, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 2 arriving orders as demand proxy
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Order amount with smoothing to avoid extreme fluctuations
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to prevent large order swings
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
