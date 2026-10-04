# policy_hash: 4cb2f2f1059b5bd4053d0c3e0071c3d8400487c93593d3187f9eea032acf625f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 42
# source_prompt_files: 2
# best_target_performance: 6162.66
# best_prompt_performance: 6162.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082836.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 528.474144926211  # OPT_PARAM: {"initial": 528.474144926211, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.10000000000167847  # OPT_PARAM: {"initial": 0.10000000000167847, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 2 arriving orders as demand proxy
    recent_arrivals = []
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]
    elif pipeline_orders:
        recent_arrivals = pipeline_orders[:1]

    forecast_demand = 0.0
    if recent_arrivals:
        forecast_demand = sum(recent_arrivals) / len(recent_arrivals)

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * forecast_demand

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, target_position - net_inventory)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.1394254714462126  # OPT_PARAM: {"initial": 0.1394254714462126, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}

    # Only place order if significant enough
    if raw_order < min_order_threshold:
        order_amount = 0
    else:
        # Smooth the order amount
        order_amount = int(smoothing_factor * raw_order)

    return order_amount
