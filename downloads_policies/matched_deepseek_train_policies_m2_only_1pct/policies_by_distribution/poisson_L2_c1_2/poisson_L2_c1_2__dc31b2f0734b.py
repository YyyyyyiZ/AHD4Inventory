# policy_hash: dc31b2f0734bec3abf2ca1d217906f14ca431ee167058bab2e56996d618751cc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 862.08
# best_prompt_performance: 862.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_102234.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.74184411991075  # OPT_PARAM: {"initial": 283.74184411991075, "min": 260, "max": 320, "type": "float"}
    safety_stock = 26.950590479933744  # OPT_PARAM: {"initial": 26.950590479933744, "min": 15, "max": 40, "type": "float"}
    demand_adjustment = 0.8914878427064624  # OPT_PARAM: {"initial": 0.8914878427064624, "min": 0.85, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2889881094394972  # OPT_PARAM: {"initial": 0.2889881094394972, "min": 0.2, "max": 0.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
    threshold_high = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 0.95, "type": "float"}
    threshold_low = 0.3602202614876414  # OPT_PARAM: {"initial": 0.3602202614876414, "min": 0.1, "max": 0.4, "type": "float"}
    reduction_factor = 0.55  # OPT_PARAM: {"initial": 0.55, "min": 0.4, "max": 0.7, "type": "float"}
    boost_factor = 1.2491910042526362  # OPT_PARAM: {"initial": 1.2491910042526362, "min": 1.1, "max": 1.6, "type": "float"}
    lost_sales_weight = 1.8676137653272684  # OPT_PARAM: {"initial": 1.8676137653272684, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Use more recent pipeline orders as demand proxy with better weighting
        recent_demand_estimate = (pipeline_orders[0] * 0.8 + pipeline_orders[1] * 0.2) * demand_adjustment
    else:
        recent_demand_estimate = 100.0 * demand_adjustment

    # Dynamic base stock with safety buffer adjusted for lost sales cost
    # Higher lost sales cost (p=2) vs holding cost (h=1) suggests we should carry more inventory
    dynamic_base = base_stock + safety_stock * lost_sales_weight - recent_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_base - net_inventory)

    # Apply smoothing with pipeline consideration
    smoothed_order = raw_order * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)

    # Adjust based on pipeline fullness with more aggressive thresholds
    pipeline_total = sum(pipeline_orders)
    if pipeline_total > base_stock * threshold_high:
        smoothed_order *= reduction_factor
    elif pipeline_total < base_stock * threshold_low:
        smoothed_order *= boost_factor

    # Ensure order is integer
    order_amount = int(round(smoothed_order))

    return order_amount
