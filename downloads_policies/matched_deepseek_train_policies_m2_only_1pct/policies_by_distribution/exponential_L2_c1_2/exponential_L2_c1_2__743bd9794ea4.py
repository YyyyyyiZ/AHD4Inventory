# policy_hash: 743bd9794ea45c983e1e7009f4443fa828115f6a7ccc03180857adec1c94e174
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 5881.44
# best_prompt_performance: 5881.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230424.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 169.5276692939468  # OPT_PARAM: {"initial": 169.5276692939468, "min": 100, "max": 300, "type": "float"}
    safety_multiplier = 2.5414449493719276  # OPT_PARAM: {"initial": 2.5414449493719276, "min": 1.0, "max": 4.0, "type": "float"}
    pipeline_weight = 1.030446337945326  # OPT_PARAM: {"initial": 1.030446337945326, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from pipeline orders (more stable than historical)
    if len(pipeline_orders) >= 3:
        # Use weighted average of last 3 pipeline orders
        weights = [0.2, 0.3, 0.5]  # More weight to recent orders
        recent_demand = sum(w * p for w, p in zip(weights, pipeline_orders[-3:]))
    else:
        recent_demand = base_stock * 0.4

    # Calculate safety stock
    safety_stock = safety_multiplier * recent_demand

    # Target inventory position
    target_position = base_stock + safety_stock

    # Adjust for pipeline coverage
    pipeline_cover = pipeline_weight * recent_demand * len(pipeline_orders)
    pipeline_adjustment = max(0, pipeline_cover - sum(pipeline_orders))

    # Final target
    final_target = target_position + pipeline_adjustment

    # Order needed
    order_needed = final_target - inventory_position

    # Apply smoothing
    smoothed_order = smoothing_factor * order_needed

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
