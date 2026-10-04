# policy_hash: c5217c39d40958e8ea9683cf870485965fcc906ca4d764a981011b5f1087ba6f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 3517.23
# best_prompt_performance: 3517.23
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_064258.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 438.2018209826472  # OPT_PARAM: {"initial": 438.2018209826472, "min": 350, "max": 500, "type": "float"}
    safety_stock = 63.20182098264298  # OPT_PARAM: {"initial": 63.20182098264298, "min": 30, "max": 70, "type": "float"}
    demand_multiplier = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    max_order = 97.8092333959012  # OPT_PARAM: {"initial": 97.8092333959012, "min": 90, "max": 150, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 30, "type": "float"}
    smoothing_factor = 0.5559251651340127  # OPT_PARAM: {"initial": 0.5559251651340127, "min": 0.2, "max": 0.6, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline orders
    if len(pipeline_orders) >= 2:
        # More balanced weighting for better stability
        recent_demand = (pipeline_orders[0] * 0.5 + pipeline_orders[1] * 0.3 +
                        (pipeline_orders[2] if len(pipeline_orders) > 2 else pipeline_orders[0]) * 0.2)
    elif pipeline_orders:
        recent_demand = pipeline_orders[0]
    else:
        recent_demand = 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + demand_multiplier * recent_demand

    # Incorporate pipeline information with adjusted weight
    if len(pipeline_orders) > 1:
        pipeline_effect = pipeline_weight * sum(pipeline_orders[1:])
    else:
        pipeline_effect = 0

    # Calculate order-up-to level
    order_up_to = adjusted_base + safety_stock - pipeline_effect

    # Calculate raw order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing
    if hasattr(compute_order_amount, 'prev_order'):
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * compute_order_amount.prev_order

    # Apply order bounds
    order_amount = min(max(order_amount, min_order), max_order)

    # Store for next smoothing
    compute_order_amount.prev_order = order_amount

    # Ensure integer order amount
    return order_amount
