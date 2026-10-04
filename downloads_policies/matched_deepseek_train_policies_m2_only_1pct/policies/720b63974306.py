# policy_hash: 720b639743068207647a5a463c16e0d9c9ba2f3c9570384228ca131d1375d69a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 845.82
# best_prompt_performance: 845.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001211.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 507.2877055949582  # OPT_PARAM: {"initial": 507.2877055949582, "min": 400, "max": 650, "type": "float"}
    safety_stock = 22.28770559495762  # OPT_PARAM: {"initial": 22.28770559495762, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 94.63195194899576  # OPT_PARAM: {"initial": 94.63195194899576, "min": 85, "max": 115, "type": "float"}
    pipeline_weight = 0.7173939906429303  # OPT_PARAM: {"initial": 0.7173939906429303, "min": 0.4, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    order_threshold = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with pipeline adjustment
    # Use weighted average of recent pipeline orders instead of just the latest
    recent_pipeline = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
    pipeline_adjustment = pipeline_weight * recent_pipeline

    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Calculate order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply threshold-based ordering to reduce small, frequent orders
    if order_needed > demand_forecast * order_threshold:
        # Smooth ordering with demand forecast
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
