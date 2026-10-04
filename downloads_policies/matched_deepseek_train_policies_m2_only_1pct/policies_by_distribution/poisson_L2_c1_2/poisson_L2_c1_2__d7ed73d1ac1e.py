# policy_hash: d7ed73d1ac1e4be05d716a92d5a060ee6ba260b64b59f2ecb70b43ac470afb4f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 773.94
# best_prompt_performance: 773.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_102408.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 321.67769312415544  # OPT_PARAM: {"initial": 321.67769312415544, "min": 280, "max": 340, "type": "float"}
    safety_stock = 30.43602061845955  # OPT_PARAM: {"initial": 30.43602061845955, "min": 20, "max": 35, "type": "float"}
    demand_adjustment = 0.8144212023352765  # OPT_PARAM: {"initial": 0.8144212023352765, "min": 0.75, "max": 0.95, "type": "float"}
    smoothing_factor = 0.30064192130012846  # OPT_PARAM: {"initial": 0.30064192130012846, "min": 0.25, "max": 0.45, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 0.6, "type": "float"}
    threshold_high = 0.75  # OPT_PARAM: {"initial": 0.75, "min": 0.6, "max": 0.85, "type": "float"}
    threshold_low = 0.2993580786998715  # OPT_PARAM: {"initial": 0.2993580786998715, "min": 0.15, "max": 0.35, "type": "float"}
    boost_factor = 1.1869923331089192  # OPT_PARAM: {"initial": 1.1869923331089192, "min": 1.1, "max": 1.4, "type": "float"}
    reduce_factor = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.5, "max": 0.8, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Use more recent pipeline orders as demand proxy
        recent_demand_estimate = (pipeline_orders[0] * 0.7 + pipeline_orders[1] * 0.3) * demand_adjustment
    else:
        recent_demand_estimate = 100.0 * demand_adjustment

    # Dynamic base stock with safety buffer
    dynamic_base = base_stock + safety_stock - recent_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_base - net_inventory)

    # Apply smoothing with pipeline consideration
    smoothed_order = raw_order * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)

    # Adjust based on pipeline fullness
    pipeline_total = sum(pipeline_orders)
    if pipeline_total > base_stock * threshold_high:
        smoothed_order *= reduce_factor
    elif pipeline_total < base_stock * threshold_low:
        smoothed_order *= boost_factor

    order_amount = int(round(smoothed_order))

    return order_amount
