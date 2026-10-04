# policy_hash: f83adfa42c7027fb80be3bbc41e20d7b992d6f5f428fee9ea4f4011ae04f2dbd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 2
# best_target_performance: 4118.16
# best_prompt_performance: 4118.54
# best_rel_error_pct: 0.009227
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_231616.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 577.1767587862691  # OPT_PARAM: {"initial": 577.1767587862691, "min": 300, "max": 800, "type": "float"}
    safety_stock = 57.80030734831096  # OPT_PARAM: {"initial": 57.80030734831096, "min": 30, "max": 150, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    demand_forecast_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.2, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall
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
