# policy_hash: 18a56d3f358e903947d9660ac181e2549a3beb813969fe012343b3d8e78c2918
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 40
# source_prompt_files: 3
# best_target_performance: 5936.66
# best_prompt_performance: 5936.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024814.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 178.36103843716575  # OPT_PARAM: {"initial": 178.36103843716575, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.514684379195064  # OPT_PARAM: {"initial": 20.514684379195064, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.36162806262684016  # OPT_PARAM: {"initial": 0.36162806262684016, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]  # Last two arrivals
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = base_stock / 4  # Fallback estimate

    # Adjust base stock based on demand pattern
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Order amount with smoothing to avoid extreme fluctuations
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid overreacting to small changes
    smoothing_factor = 0.17946635462006982  # OPT_PARAM: {"initial": 0.17946635462006982, "min": 0.1, "max": 1.0, "type": "float"}

    # Consider previous order in pipeline for smoothing
    if len(pipeline_orders) > 0:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * previous_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(smoothed_order))

    return order_amount
