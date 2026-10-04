# policy_hash: 9bf5ab501ae3721695ca39ddee474fc4cdc278e8530be6a95e0f23e91025265b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 1165.18
# best_prompt_performance: 1165.04
# best_rel_error_pct: 0.012015
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_041426.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 304.4041041805516  # OPT_PARAM: {"initial": 304.4041041805516, "min": 200, "max": 350, "type": "float"}
    demand_buffer = 12.8  # OPT_PARAM: {"initial": 12.8, "min": 5, "max": 30, "type": "float"}
    pipeline_weight = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}
    smoothing = 0.4351703513809924  # OPT_PARAM: {"initial": 0.4351703513809924, "min": 0.2, "max": 0.8, "type": "float"}
    safety_factor = 1.15  # OPT_PARAM: {"initial": 1.15, "min": 1.0, "max": 1.5, "type": "float"}

    # Inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand estimation using weighted pipeline average
    if len(pipeline_orders) >= 2:
        # Weight recent pipeline orders more heavily
        weights = [0.3, 0.7] if len(pipeline_orders) >= 2 else [1.0]
        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders[-2:]))
        recent_activity = weighted_sum / sum(weights)
        demand_estimate = recent_activity * safety_factor + demand_buffer
    else:
        demand_estimate = base_stock * 0.25

    # Dynamic pipeline adjustment
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_weight * (avg_pipeline - demand_estimate) * len(pipeline_orders)

    # Adjusted target with tighter bounds
    target = max(base_stock * 0.7, min(base_stock * 1.3, base_stock + pipeline_adjustment))

    # Calculate needed inventory
    needed = max(0, target - inventory_position)

    # Adaptive smoothing based on pipeline status
    if pipeline_orders:
        previous_order = pipeline_orders[-1]
        # Reduce smoothing when inventory is very low or high
        if inventory_position < target * 0.5:
            effective_smoothing = smoothing * 0.7
        elif inventory_position > target * 1.5:
            effective_smoothing = smoothing * 1.3
        else:
            effective_smoothing = smoothing

        order = effective_smoothing * needed + (1 - effective_smoothing) * previous_order
    else:
        order = needed

    # Ensure non-negative integer with conservative rounding
    order_amount = max(0, int(round(order)))

    return order_amount
