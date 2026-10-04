# policy_hash: 6975d0adad2a0c0e1a08a23b349c3f3c5f77d6f2ecdaec476d54ec4bca18ee7c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 12023.2
# best_prompt_performance: 12023.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003201.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 347.99441961848436  # OPT_PARAM: {"initial": 347.99441961848436, "min": 200, "max": 600, "type": "float"}
    safety_stock = 97.99441961848392  # OPT_PARAM: {"initial": 97.99441961848392, "min": 50, "max": 300, "type": "float"}
    demand_smoothing = 0.5196106515254256  # OPT_PARAM: {"initial": 0.5196106515254256, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_weight = 0.7769574496985131  # OPT_PARAM: {"initial": 0.7769574496985131, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline arrivals
    # More weight on recent arrivals
    if len(pipeline_orders) >= 2:
        # Weight recent arrivals more heavily
        weights = [pipeline_weight, 1.0 - pipeline_weight]
        weighted_sum = pipeline_orders[0] * weights[0] + pipeline_orders[1] * weights[1]
        avg_recent_demand = weighted_sum / sum(weights)
    else:
        avg_recent_demand = pipeline_orders[0] if pipeline_orders else 0

    # Smooth demand estimate
    static_demand_estimate = 100.0  # Fixed estimate based on historical average
    smoothed_demand = (demand_smoothing * avg_recent_demand +
                      (1 - demand_smoothing) * static_demand_estimate)

    # Adjust base stock based on smoothed demand
    demand_adjustment = max(0, smoothed_demand - static_demand_estimate)
    adjusted_base_stock = base_stock + 0.5 * demand_adjustment  # Conservative adjustment

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount with rounding
    order_amount = max(0, target_inventory - inventory_position)
    order_amount = int(round(order_amount))

    return order_amount
