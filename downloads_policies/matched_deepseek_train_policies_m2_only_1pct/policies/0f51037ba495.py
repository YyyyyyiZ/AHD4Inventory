# policy_hash: 0f51037ba495c81ed437cc23d748ad63200fa8eb7ef576c7f15338a09695dba9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5864.08
# best_prompt_performance: 5864.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230534.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 217.4177353396908  # OPT_PARAM: {"initial": 217.4177353396908, "min": 180, "max": 280, "type": "float"}
    safety_factor = 1.7612775901964186  # OPT_PARAM: {"initial": 1.7612775901964186, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_weight = 0.933954847351925  # OPT_PARAM: {"initial": 0.933954847351925, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.34008573197118  # OPT_PARAM: {"initial": 0.34008573197118, "min": 0.2, "max": 0.5, "type": "float"}
    demand_est_window = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 5, "type": "int"}
    pipeline_coverage_factor = 0.25981648920248696  # OPT_PARAM: {"initial": 0.25981648920248696, "min": 0.1, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals
    if len(pipeline_orders) >= demand_est_window:
        recent_arrivals = pipeline_orders[:demand_est_window]
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals)
    else:
        demand_estimate = base_stock * 0.2

    # Calculate safety stock
    safety_stock = safety_factor * demand_estimate

    # Adjust for pipeline coverage
    expected_pipeline = base_stock * len(pipeline_orders) * pipeline_weight
    current_pipeline = sum(pipeline_orders)
    pipeline_adjustment = max(0, expected_pipeline - current_pipeline) * pipeline_coverage_factor

    # Target inventory position
    target = base_stock + safety_stock + pipeline_adjustment

    # Order needed
    order_needed = target - inventory_position

    # Apply smoothing to avoid large order swings
    if abs(order_needed) > demand_estimate * 2.0:
        order_amount = order_needed * smoothing_factor
    else:
        order_amount = order_needed

    # Ensure non-negative integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
