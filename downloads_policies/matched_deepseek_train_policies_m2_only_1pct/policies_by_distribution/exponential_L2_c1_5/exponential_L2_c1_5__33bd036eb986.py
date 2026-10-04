# policy_hash: 33bd036eb986f821103ab3fe6a0ea0dea38664766adc998eb02e9b1710c6daf4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10223.66
# best_prompt_performance: 10223.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073611.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 396.35760722514016  # OPT_PARAM: {"initial": 396.35760722514016, "min": 300, "max": 600, "type": "float"}
    safety_multiplier = 3.2  # OPT_PARAM: {"initial": 3.2, "min": 2.0, "max": 5.0, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    min_order_threshold = 18.88971520868342  # OPT_PARAM: {"initial": 18.88971520868342, "min": 10, "max": 50, "type": "float"}
    demand_estimation_window = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 8, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from recent pipeline orders
    if len(pipeline_orders) >= 2:
        # Use recent orders for demand estimation
        recent_orders = pipeline_orders[:min(demand_estimation_window, len(pipeline_orders))]
        if len(recent_orders) > 1:
            mean_order = sum(recent_orders) / len(recent_orders)
            variance = sum((x - mean_order) ** 2 for x in recent_orders) / len(recent_orders)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
    else:
        std_dev = 0

    # Calculate safety stock based on variability
    safety_stock = safety_multiplier * std_dev

    # Target inventory position
    target_position = base_stock + safety_stock

    # Calculate required order
    gap = target_position - inventory_position

    # Apply adjustment factor and ensure non-negative
    if gap > min_order_threshold:
        order_amount = max(0, gap * adjustment_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
