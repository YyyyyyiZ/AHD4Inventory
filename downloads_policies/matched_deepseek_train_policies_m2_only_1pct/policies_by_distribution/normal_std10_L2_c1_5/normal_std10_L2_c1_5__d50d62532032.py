# policy_hash: d50d62532032bd96ab737a54557a496b2fc251e31384778c809fb390368f5a49
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1207.88
# best_prompt_performance: 1211.78
# best_rel_error_pct: 0.322880
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_234100.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 273.0614220293447  # OPT_PARAM: {"initial": 273.0614220293447, "min": 250, "max": 320, "type": "float"}
    safety_stock = 29.883614777897666  # OPT_PARAM: {"initial": 29.883614777897666, "min": 20, "max": 50, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.7, "type": "float"}
    lead_time = 2  # OPT_PARAM: {"initial": 2, "min": 2, "max": 2, "type": "int"}
    avg_demand = 95.60083576308102  # OPT_PARAM: {"initial": 95.60083576308102, "min": 90, "max": 110, "type": "float"}
    demand_std = 10.635457144590157  # OPT_PARAM: {"initial": 10.635457144590157, "min": 8, "max": 20, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety buffer
    expected_lead_time_demand = lead_time * avg_demand
    safety_buffer = demand_std * (lead_time ** 0.5) * 1.5

    # Dynamic target based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (lead_time * avg_demand) if lead_time * avg_demand > 0 else 1.0
    pipeline_adjustment = 0.0
    if pipeline_ratio < 0.8:
        pipeline_adjustment = 15.0
    elif pipeline_ratio > 1.2:
        pipeline_adjustment = -10.0

    # Target inventory position
    target_position = base_stock + safety_stock + expected_lead_time_demand + safety_buffer + pipeline_adjustment

    # Calculate raw order needed
    raw_order = target_position - inventory_position

    # Apply smoothing with asymmetric adjustment
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order
    elif raw_order < -20:  # Only smooth large negative adjustments
        smoothed_order = 0.3 * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
