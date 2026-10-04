# policy_hash: 772b3a864bf077a52025604c0d772f9a8da0b4da025577532e39d3fd6c937e2c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5879.92
# best_prompt_performance: 5879.94
# best_rel_error_pct: 0.000340
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225521.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 204.54838515644974  # OPT_PARAM: {"initial": 204.54838515644974, "min": 150, "max": 300, "type": "float"}
    safety_factor = 2.0705708484563994  # OPT_PARAM: {"initial": 2.0705708484563994, "min": 1.5, "max": 3.5, "type": "float"}
    pipeline_coverage = 0.7166873489998719  # OPT_PARAM: {"initial": 0.7166873489998719, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.28593934363009715  # OPT_PARAM: {"initial": 0.28593934363009715, "min": 0.2, "max": 0.6, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand estimate from recent pipeline orders
    if len(pipeline_orders) >= 2:
        recent_demand_est = sum(pipeline_orders[-2:]) / 2
    else:
        recent_demand_est = base_stock * 0.3

    # Safety stock based on recent demand
    safety_stock = safety_factor * recent_demand_est

    # Expected pipeline coverage
    expected_pipeline = base_stock * len(pipeline_orders) * pipeline_coverage
    current_pipeline = sum(pipeline_orders)

    # Target inventory position
    target = base_stock + safety_stock + max(0, expected_pipeline - current_pipeline) * 0.3

    # Order needed
    order_needed = target - inventory_position

    # Apply smoothing
    if abs(order_needed) > base_stock * 0.4:
        order_amount = order_needed * smoothing
    else:
        order_amount = order_needed

    # Ensure non-negative integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
