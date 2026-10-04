# policy_hash: c73fb8ba52e7de9359950c380cfa09b047f8c23c464088197f163ba5857c1078
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4208.64
# best_prompt_performance: 4208.3
# best_rel_error_pct: 0.008079
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230402.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 533.7885375343315  # OPT_PARAM: {"initial": 533.7885375343315, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.86583105810962  # OPT_PARAM: {"initial": 49.86583105810962, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.28363805810879295  # OPT_PARAM: {"initial": 0.28363805810879295, "min": 0.1, "max": 0.9, "type": "float"}
    demand_forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall with smoothing
    expected_shortfall = max(0, base_stock - inventory_position)

    # Add safety stock adjustment
    adjusted_shortfall = expected_shortfall + safety_stock

    # Apply demand forecast adjustment based on recent pipeline arrivals
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[0] if pipeline_orders[0] > 0 else 0
        forecast_adjustment = demand_forecast_factor * recent_arrivals
        adjusted_shortfall = max(0, adjusted_shortfall + forecast_adjustment)

    # Apply pipeline weighting to reduce order volatility
    pipeline_influence = pipeline_weight * sum(pipeline_orders)
    adjusted_shortfall = max(0, adjusted_shortfall - pipeline_influence)

    # Apply smoothing to avoid large order swings
    order_amount = max(0, smoothing_factor * adjusted_shortfall)

    # Round to nearest integer for practical ordering
    order_amount = int(round(order_amount))

    return order_amount
