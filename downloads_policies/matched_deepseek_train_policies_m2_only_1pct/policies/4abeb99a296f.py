# policy_hash: 4abeb99a296f25d11b4162e80fa71a9dacb9e59679d0373558707a765e100258
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 6074.88
# best_prompt_performance: 6074.92
# best_rel_error_pct: 0.000658
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064738.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 213.20515244138284  # OPT_PARAM: {"initial": 213.20515244138284, "min": 100, "max": 400, "type": "float"}
    safety_multiplier = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing_factor = 0.475949567950713  # OPT_PARAM: {"initial": 0.475949567950713, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate safety stock based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_var = sum((x - pipeline_mean) ** 2 for x in pipeline_orders) / len(pipeline_orders)
        safety_stock = safety_multiplier * (pipeline_var ** 0.5)
    else:
        safety_stock = 0.0

    # Adjust target based on pipeline composition
    immediate_arrival = pipeline_orders[0] if pipeline_orders else 0
    future_arrivals = sum(pipeline_orders[1:]) if len(pipeline_orders) > 1 else 0

    # Target inventory position considers both base stock and pipeline status
    target_position = base_stock + safety_stock
    if future_arrivals > 0:
        target_position += pipeline_weight * future_arrivals

    # Smooth ordering to avoid large swings
    order_gap = target_position - inventory_position
    if order_gap > 0:
        # Apply smoothing to order quantity
        smoothed_order = smoothing_factor * order_gap + (1 - smoothing_factor) * immediate_arrival
    else:
        smoothed_order = 0.0

    # Round to integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))
    return order_amount
