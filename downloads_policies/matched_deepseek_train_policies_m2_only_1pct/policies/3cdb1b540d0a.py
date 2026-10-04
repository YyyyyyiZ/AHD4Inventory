# policy_hash: 3cdb1b540d0a2b6524f56359a23f0297cff3558acd9f1456eebeae71c6aebea7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 5879.8
# best_prompt_performance: 5879.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230054.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 183.00235608767565  # OPT_PARAM: {"initial": 183.00235608767565, "min": 100, "max": 300, "type": "float"}
    safety_multiplier = 1.0612159617390076  # OPT_PARAM: {"initial": 1.0612159617390076, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_weight = 0.5616385445499728  # OPT_PARAM: {"initial": 0.5616385445499728, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3066213929895456  # OPT_PARAM: {"initial": 0.3066213929895456, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals (proxy for recent demand)
    if len(pipeline_orders) >= 2:
        # Use weighted average with more weight on recent orders
        recent_demand_est = pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4
    else:
        recent_demand_est = base_stock * 0.5

    # Calculate safety stock based on recent demand variability
    safety_stock = safety_multiplier * recent_demand_est

    # Adjust target based on pipeline status
    # If pipeline is empty, increase order; if full, reduce order
    pipeline_avg = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = (base_stock - pipeline_avg) * pipeline_weight

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + pipeline_adjustment

    # Calculate needed order
    order_needed = target_inventory - inventory_position

    # Apply smoothing to avoid extreme fluctuations
    smoothed_order = order_needed * smoothing_factor

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
