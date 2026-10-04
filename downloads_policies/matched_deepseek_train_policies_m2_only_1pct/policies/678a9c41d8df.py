# policy_hash: 678a9c41d8dfd40ac7eaf2ec4cc97f1d24772dc3d5af7e87ff8b2b51b15654a4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 11310.81
# best_prompt_performance: 11310.48
# best_rel_error_pct: 0.002918
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005333.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 370.83993203645883  # OPT_PARAM: {"initial": 370.83993203645883, "min": 100, "max": 800, "type": "float"}
    safety_stock = 120.3  # OPT_PARAM: {"initial": 120.3, "min": 50, "max": 300, "type": "float"}
    demand_forecast_factor = 0.7023804133645949  # OPT_PARAM: {"initial": 0.7023804133645949, "min": 0.1, "max": 2.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    pipeline_weight = 0.9235908587220152  # OPT_PARAM: {"initial": 0.9235908587220152, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use weighted average of pipeline orders as demand forecast
    # More weight to recent orders
    if pipeline_orders:
        weighted_sum = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders):
            weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
            weighted_sum += order * weight
            total_weight += weight
        avg_weighted_demand = weighted_sum / total_weight
    else:
        avg_weighted_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_weighted_demand

    # Add safety stock adjustment
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate raw order
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing using last order if available
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
