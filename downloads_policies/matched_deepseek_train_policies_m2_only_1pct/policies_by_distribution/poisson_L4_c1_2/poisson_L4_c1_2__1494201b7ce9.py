# policy_hash: 1494201b7ce91a827f50fa9b7c3d03a5d4d3c574cef11d35fd1b0705e9cb20bf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 917.02
# best_prompt_performance: 917.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001853.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 479.8464444415855  # OPT_PARAM: {"initial": 479.8464444415855, "min": 380, "max": 480, "type": "float"}
    safety_stock = 59.920320769961336  # OPT_PARAM: {"initial": 59.920320769961336, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    order_threshold = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 4, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline adjustment using weighted average of recent pipeline orders
    lookback = min(pipeline_lookback, len(pipeline_orders))
    recent_pipeline = sum(pipeline_orders[-lookback:]) / lookback if lookback > 0 else 0
    pipeline_adjustment = pipeline_weight * recent_pipeline

    # Target inventory level
    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing with threshold
    if order_needed > demand_forecast * order_threshold:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
