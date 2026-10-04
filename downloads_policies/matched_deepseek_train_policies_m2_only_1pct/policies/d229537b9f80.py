# policy_hash: d229537b9f8051d17a9f1b42b1028ba8d9b1267cde240ad24ef9d9e8110041ff
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 812.82
# best_prompt_performance: 812.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103538.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 303.4739647078287  # OPT_PARAM: {"initial": 303.4739647078287, "min": 250, "max": 350, "type": "float"}
    safety_stock = 34.273470996562125  # OPT_PARAM: {"initial": 34.273470996562125, "min": 15, "max": 40, "type": "float"}
    demand_adjustment = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.7, "type": "float"}
    pipeline_threshold_high = 0.75  # OPT_PARAM: {"initial": 0.75, "min": 0.6, "max": 0.9, "type": "float"}
    pipeline_threshold_low = 0.30000000000000004  # OPT_PARAM: {"initial": 0.30000000000000004, "min": 0.1, "max": 0.4, "type": "float"}
    high_multiplier = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.5, "max": 0.8, "type": "float"}
    low_multiplier = 1.15136616116983  # OPT_PARAM: {"initial": 1.15136616116983, "min": 1.1, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Use more recent pipeline orders as demand proxy
        recent_demand_estimate = (pipeline_orders[0] * pipeline_weight + pipeline_orders[1] * (1 - pipeline_weight)) * demand_adjustment
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
    if pipeline_total > base_stock * pipeline_threshold_high:
        smoothed_order *= high_multiplier
    elif pipeline_total < base_stock * pipeline_threshold_low:
        smoothed_order *= low_multiplier

    order_amount = int(round(smoothed_order))

    return order_amount
