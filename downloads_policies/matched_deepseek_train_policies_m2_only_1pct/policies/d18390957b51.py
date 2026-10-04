# policy_hash: d18390957b51d2e08910995cb0bce2a6af02093b0a7093ea92435837a5a05115
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2821.48
# best_prompt_performance: 2818.96
# best_rel_error_pct: 0.089315
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_164704.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 696.6897656481864  # OPT_PARAM: {"initial": 696.6897656481864, "min": 500, "max": 1000, "type": "float"}
    safety_stock = 66.40332188418637  # OPT_PARAM: {"initial": 66.40332188418637, "min": 40, "max": 150, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_estimate_factor = 1.4370678348572887  # OPT_PARAM: {"initial": 1.4370678348572887, "min": 0.8, "max": 1.5, "type": "float"}
    min_order_threshold = 0.37094710616609705  # OPT_PARAM: {"initial": 0.37094710616609705, "min": 0.05, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use more recent orders for better demand estimation
        lookback = min(4, len(pipeline_orders))
        recent_orders = pipeline_orders[-lookback:]
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 100.0

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock * demand_estimate_factor

    # Calculate required order
    required_order = max(0, target_inventory - inventory_position)

    # Apply smoothing and round to integer
    smoothed_order = smoothing_factor * required_order

    # Only place order if significant enough
    if smoothed_order < avg_recent_demand * min_order_threshold:
        order_amount = 0
    else:
        order_amount = int(round(smoothed_order))

    return order_amount
