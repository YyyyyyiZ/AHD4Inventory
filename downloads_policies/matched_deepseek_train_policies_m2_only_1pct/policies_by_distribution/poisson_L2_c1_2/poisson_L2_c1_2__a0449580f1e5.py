# policy_hash: a0449580f1e57a71890102518b8e96934fb278940b83b1f08022aac96701ed95
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 114
# source_prompt_files: 1
# best_target_performance: 781.4
# best_prompt_performance: 781.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_100822.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 325.86039774697747  # OPT_PARAM: {"initial": 325.86039774697747, "min": 200, "max": 400, "type": "float"}
    safety_stock = 37.875966143532075  # OPT_PARAM: {"initial": 37.875966143532075, "min": 10, "max": 50, "type": "float"}
    demand_adjustment = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2253012501488849  # OPT_PARAM: {"initial": 0.2253012501488849, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Weight recent arrivals more heavily
        recent_demand_estimate = (pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4) * demand_adjustment
    else:
        recent_demand_estimate = 100.0 * demand_adjustment

    # Dynamic base stock with safety buffer
    dynamic_base = base_stock + safety_stock - recent_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_base - net_inventory)

    # Apply exponential smoothing to reduce order volatility
    order_amount = int(round(raw_order * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)))

    return order_amount
