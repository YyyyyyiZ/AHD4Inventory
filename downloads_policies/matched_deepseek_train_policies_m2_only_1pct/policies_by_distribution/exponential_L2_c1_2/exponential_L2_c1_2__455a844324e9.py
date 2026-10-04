# policy_hash: 455a844324e901ba19ef6e031766301e0351fa7d73d0ed069fe536ac39722d23
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 2
# best_target_performance: 5878.12
# best_prompt_performance: 5878.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225757.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 260.429850268576  # OPT_PARAM: {"initial": 260.429850268576, "min": 180, "max": 280, "type": "float"}
    safety_factor = 2.361640736577001  # OPT_PARAM: {"initial": 2.361640736577001, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_weight = 0.8537318684841021  # OPT_PARAM: {"initial": 0.8537318684841021, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_est_window = 3  # OPT_PARAM: {"initial": 3, "min": 2, "max": 5, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals (which reflect past orders)
    if len(pipeline_orders) >= demand_est_window:
        recent_arrivals = pipeline_orders[:demand_est_window]
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals)
    else:
        demand_estimate = base_stock * 0.25

    # Calculate safety stock
    safety_stock = safety_factor * demand_estimate

    # Adjust for pipeline coverage
    expected_pipeline = base_stock * len(pipeline_orders) * pipeline_weight
    current_pipeline = sum(pipeline_orders)
    pipeline_adjustment = max(0, expected_pipeline - current_pipeline) * 0.25

    # Target inventory position
    target = base_stock + safety_stock + pipeline_adjustment

    # Order needed
    order_needed = target - inventory_position

    # Apply smoothing to avoid large order swings
    if abs(order_needed) > demand_estimate * 2.5:
        order_amount = order_needed * smoothing_factor
    else:
        order_amount = order_needed

    # Ensure non-negative integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
