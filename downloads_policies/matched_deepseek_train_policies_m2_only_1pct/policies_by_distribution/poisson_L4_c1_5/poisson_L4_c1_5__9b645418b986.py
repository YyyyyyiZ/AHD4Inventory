# policy_hash: 9b645418b986d2dd1017f4e95c2fdc90b3c4f953118287dea3d8f46f597301bc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 2274.55
# best_prompt_performance: 2274.55
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081355.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 504.2378358737853  # OPT_PARAM: {"initial": 504.2378358737853, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 40, "max": 120, "type": "float"}
    demand_adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using recent pipeline arrivals
    # Use weighted average of recent orders to estimate demand
    if len(pipeline_orders) >= 2:
        # More weight on recent orders
        recent_estimate = (pipeline_orders[-1] * 0.6 + pipeline_orders[-2] * 0.4)
    elif pipeline_orders:
        recent_estimate = pipeline_orders[-1]
    else:
        recent_estimate = 100.0  # Default estimate

    # Smooth the demand estimate
    demand_estimate = recent_estimate * smoothing_factor + 100 * (1 - smoothing_factor)

    # Adjust base stock based on demand estimate
    demand_deviation = demand_estimate - 100
    adjusted_base = base_stock + demand_deviation * demand_adjustment_factor

    # Apply safety stock adjustment
    order_up_to = max(adjusted_base, base_stock - safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply ordering discipline: round to nearest integer
    return order_amount
