# policy_hash: 44a858b6740ffbf99f6325da35aec6a1ea4a0148619a404ac077bb7362e13ed6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1029.62
# best_prompt_performance: 1029.88
# best_rel_error_pct: 0.025252
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_062618.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.7427476520498  # OPT_PARAM: {"initial": 286.7427476520498, "min": 280, "max": 340, "type": "float"}
    safety_stock = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 5, "max": 15, "type": "float"}
    demand_smoothing = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.4, "max": 0.8, "type": "float"}
    pipeline_weight = 0.09832289455038995  # OPT_PARAM: {"initial": 0.09832289455038995, "min": 0.05, "max": 0.3, "type": "float"}
    adjustment_factor = 0.15798747346092662  # OPT_PARAM: {"initial": 0.15798747346092662, "min": 0.1, "max": 0.4, "type": "float"}
    order_threshold = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals (more responsive)
    if len(pipeline_orders) >= 2:
        # Use weighted average favoring most recent
        recent_estimate = pipeline_orders[0] * 0.8 + pipeline_orders[1] * 0.2
    else:
        recent_estimate = base_stock / 3.0

    # Smooth demand estimate with stronger recent weighting
    smoothed_demand = demand_smoothing * recent_estimate + (1 - demand_smoothing) * (base_stock / 3.0)

    # Adjust base stock based on pipeline status
    pipeline_avg = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_weight * (pipeline_avg - base_stock / 3.0)

    # Calculate target inventory position with reduced adjustment
    target_position = base_stock + safety_stock + adjustment_factor * pipeline_adjustment

    # Calculate order amount
    order_needed = target_position - inventory_position

    # Apply higher order threshold to reduce small orders
    if order_needed > order_threshold:
        order_amount = int(round(order_needed))
    else:
        order_amount = 0

    return order_amount
