# policy_hash: db1404c60373687a0bd31cf5990d65d40200e75dcdef562f7997955b6d5ed8dd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 799.84
# best_prompt_performance: 799.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104321.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 342.83200696382977  # OPT_PARAM: {"initial": 342.83200696382977, "min": 250, "max": 400, "type": "float"}
    safety_stock = 37.125886813127174  # OPT_PARAM: {"initial": 37.125886813127174, "min": 10, "max": 50, "type": "float"}
    demand_adjustment = 0.8295113312979138  # OPT_PARAM: {"initial": 0.8295113312979138, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.20262076042844554  # OPT_PARAM: {"initial": 0.20262076042844554, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    recent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.8, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 20, "type": "int"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent arrivals
    if len(pipeline_orders) >= 2:
        # Use recent pipeline arrivals with adjustable weighting
        recent_demand_estimate = (pipeline_orders[0] * recent_weight +
                                 pipeline_orders[1] * (1 - recent_weight)) * demand_adjustment
    else:
        recent_demand_estimate = 100.0 * demand_adjustment

    # Dynamic base stock with safety buffer
    dynamic_base = base_stock + safety_stock - recent_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_base - net_inventory)

    # Apply smoothing with pipeline consideration
    smoothed_order = raw_order * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)

    # Final adjustment based on pipeline weight
    order_amount = int(round(smoothed_order * pipeline_weight))

    # Ensure minimum order amount
    order_amount = max(min_order, order_amount)

    return order_amount
