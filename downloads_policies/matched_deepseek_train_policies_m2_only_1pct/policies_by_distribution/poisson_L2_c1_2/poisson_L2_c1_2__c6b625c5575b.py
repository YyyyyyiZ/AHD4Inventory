# policy_hash: c6b625c5575b3864a29864454bc5abedd21c7016a4470b7af021267de0b33120
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 818.28
# best_prompt_performance: 818.12
# best_rel_error_pct: 0.019553
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103127.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 345.2127259369174  # OPT_PARAM: {"initial": 345.2127259369174, "min": 250, "max": 400, "type": "float"}
    safety_stock = 30.21272593691855  # OPT_PARAM: {"initial": 30.21272593691855, "min": 10, "max": 50, "type": "float"}
    demand_adjustment = 0.7445115548394243  # OPT_PARAM: {"initial": 0.7445115548394243, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.4776409159498399  # OPT_PARAM: {"initial": 0.4776409159498399, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.9692566365302013  # OPT_PARAM: {"initial": 0.9692566365302013, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent arrivals
    if len(pipeline_orders) >= 2:
        # Use more recent pipeline arrivals for demand estimation
        recent_demand_estimate = (pipeline_orders[0] * 0.7 + pipeline_orders[1] * 0.3) * demand_adjustment
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

    return order_amount
