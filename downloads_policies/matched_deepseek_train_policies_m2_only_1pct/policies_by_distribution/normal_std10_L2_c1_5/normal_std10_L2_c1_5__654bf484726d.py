# policy_hash: 654bf484726d7e4d80abdcdcbc2ca0d91371fe2094a7de04644dec4202894017
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 1135.44
# best_prompt_performance: 1131.84
# best_rel_error_pct: 0.317058
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_042753.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.48808173417814  # OPT_PARAM: {"initial": 310.48808173417814, "min": 250, "max": 320, "type": "float"}
    demand_buffer = 7.7419498022806295  # OPT_PARAM: {"initial": 7.7419498022806295, "min": 5, "max": 15, "type": "float"}
    pipeline_weight = 0.12165725076067128  # OPT_PARAM: {"initial": 0.12165725076067128, "min": 0.05, "max": 0.2, "type": "float"}
    smoothing = 0.5381919094087706  # OPT_PARAM: {"initial": 0.5381919094087706, "min": 0.4, "max": 0.9, "type": "float"}
    safety_factor = 1.156320867502128  # OPT_PARAM: {"initial": 1.156320867502128, "min": 1.0, "max": 1.3, "type": "float"}
    lost_sales_weight = 0.5881981818359677  # OPT_PARAM: {"initial": 0.5881981818359677, "min": 0.5, "max": 1.2, "type": "float"}

    # Inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simplified demand estimation using recent pipeline orders
    if pipeline_orders:
        # Use average of last two pipeline orders as demand proxy
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        avg_recent = sum(recent_orders) / len(recent_orders)
        demand_estimate = avg_recent * safety_factor + demand_buffer
    else:
        demand_estimate = base_stock * 0.2

    # Pipeline adjustment based on deviation from demand estimate
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_adjustment = pipeline_weight * (avg_pipeline - demand_estimate) * len(pipeline_orders)
    else:
        pipeline_adjustment = 0

    # Target inventory with tighter bounds
    target = max(base_stock * 0.8, min(base_stock * 1.2, base_stock + pipeline_adjustment))

    # Calculate needed inventory with lost-sales cost consideration
    needed = max(0, target - inventory_position)

    # Apply smoothing with previous order if available
    if pipeline_orders:
        previous_order = pipeline_orders[-1]
        # Adjust smoothing based on urgency (lost sales cost is higher)
        if inventory_position < target * 0.6:
            effective_smoothing = smoothing * lost_sales_weight
        else:
            effective_smoothing = smoothing

        order = effective_smoothing * needed + (1 - effective_smoothing) * previous_order
    else:
        order = needed

    # Ensure non-negative integer
    order_amount = max(0, int(round(order)))

    return order_amount
