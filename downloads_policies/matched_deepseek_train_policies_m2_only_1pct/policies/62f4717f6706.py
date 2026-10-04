# policy_hash: 62f4717f670627749380dcbe314eefc8887c141e17c3b9a2cebb450fbf71d173
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1090.8
# best_prompt_performance: 1090.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000558.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 484.0284252039516  # OPT_PARAM: {"initial": 484.0284252039516, "min": 300, "max": 500, "type": "float"}
    safety_stock = 59.77502079267663  # OPT_PARAM: {"initial": 59.77502079267663, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.5507817903709151  # OPT_PARAM: {"initial": 0.5507817903709151, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    order_threshold = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with pipeline adjustment
    # Use weighted average of recent pipeline orders instead of just the last one
    recent_pipeline = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
    pipeline_adjustment = pipeline_weight * recent_pipeline

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_std = max(5.0, (max(pipeline_orders) - min(pipeline_orders)) / 2)
        adjusted_safety = safety_stock + 0.1 * pipeline_std
    else:
        adjusted_safety = safety_stock

    target_inventory = base_stock + adjusted_safety - pipeline_adjustment

    # Calculate order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing with demand forecast consideration
    if order_needed > order_threshold * demand_forecast:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    elif order_needed > 0:
        smoothed_order = order_needed
    else:
        smoothed_order = 0

    # Ensure non-negative order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
