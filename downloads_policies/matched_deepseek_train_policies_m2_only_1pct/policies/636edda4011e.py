# policy_hash: 636edda4011e59e4d0e09288393f36840d7ec722c5c64cda38f58f5c10ead49e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6736.14
# best_prompt_performance: 6736.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223042.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 206.98838718904688  # OPT_PARAM: {"initial": 206.98838718904688, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.10769388836486  # OPT_PARAM: {"initial": 49.10769388836486, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Weight recent pipeline orders more heavily
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[-1] * 0.6 + pipeline_orders[-2] * 0.4) * demand_buffer
    elif len(pipeline_orders) == 1:
        recent_demand_estimate = pipeline_orders[-1] * demand_buffer
    else:
        recent_demand_estimate = 0

    # Dynamic target that considers both base stock and recent demand patterns
    dynamic_target = max(base_stock, safety_stock + recent_demand_estimate)

    # Order amount with smoothing to avoid extreme fluctuations
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply smoothing: don't reduce orders too aggressively when inventory is high
    if raw_order < 0.3 * dynamic_target and inventory_position > 0.7 * dynamic_target:
        order_amount = 0
    else:
        order_amount = raw_order

    return order_amount
