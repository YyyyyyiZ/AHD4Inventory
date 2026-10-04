# policy_hash: 59a374c04cd9143a79e831d58c7aa81e73254593249638c9c0130b5e3a3cb232
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 995.46
# best_prompt_performance: 995.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_022136.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.5  # OPT_PARAM: {"initial": 310.5, "min": 250, "max": 400, "type": "float"}
    demand_estimate = 100.2  # OPT_PARAM: {"initial": 100.2, "min": 90, "max": 130, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    safety_multiplier = 1.8  # OPT_PARAM: {"initial": 1.8, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_std = max(5.0, (max(pipeline_orders) - min(pipeline_orders)) / 2.0)
        safety_stock = safety_multiplier * pipeline_std
    else:
        safety_stock = 0.0

    # Adjust target based on upcoming arrivals
    if len(pipeline_orders) > 0:
        next_arrival = pipeline_orders[0]
        if next_arrival < demand_estimate * 0.7:
            target_stock = base_stock + safety_stock * 1.5
        elif next_arrival > demand_estimate * 1.3:
            target_stock = base_stock - safety_stock * 0.5
        else:
            target_stock = base_stock + safety_stock
    else:
        target_stock = base_stock + safety_stock

    # Calculate raw order needed
    raw_order = max(0, target_stock - inventory_position)

    # Apply smoothing with pipeline consideration
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if raw_order > avg_pipeline * 1.5:
            # Large order increase - apply stronger smoothing
            order_amount = smoothing_factor * 0.7 * raw_order + (1 - smoothing_factor * 0.7) * avg_pipeline
        else:
            # Normal smoothing
            order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1]
    else:
        order_amount = raw_order

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(order_amount)))

    return order_amount
