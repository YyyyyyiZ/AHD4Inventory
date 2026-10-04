# policy_hash: 0ed33bc078b6edf1b490ae2bfadd416b62fa83b52971aad7bccc77536c9cdc45
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 11296.7
# best_prompt_performance: 11296.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004255.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 404.0479863207356  # OPT_PARAM: {"initial": 404.0479863207356, "min": 200, "max": 600, "type": "float"}
    safety_stock = 120.3  # OPT_PARAM: {"initial": 120.3, "min": 50, "max": 300, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand forecast using weighted average of pipeline orders
    # More weight to recent orders
    if pipeline_orders:
        weights = [0.7, 0.2, 0.1, 0.0][:len(pipeline_orders)]
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        avg_weighted_demand = weighted_sum / sum(weights[:len(pipeline_orders)])
    else:
        avg_weighted_demand = 0

    # Adjust base stock based on demand forecast and lead time
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_weighted_demand * lead_time_factor

    # Dynamic safety stock adjustment based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if pipeline_orders else 0
        variability_adjustment = min(pipeline_variability * 0.3, 100)
    else:
        variability_adjustment = 0

    final_safety_stock = safety_stock + variability_adjustment

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, final_safety_stock)

    # Order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Ensure order is reasonable (not too large)
    max_order_limit = 800.1  # OPT_PARAM: {"initial": 800.1, "min": 400, "max": 1500, "type": "float"}
    smoothed_order = min(smoothed_order, max_order_limit)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
