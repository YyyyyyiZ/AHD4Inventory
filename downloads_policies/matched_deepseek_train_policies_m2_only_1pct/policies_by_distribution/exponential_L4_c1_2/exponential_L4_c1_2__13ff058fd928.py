# policy_hash: 13ff058fd928040d570da25fa0086b6a883c172f286189962a5f994cc3ff0b57
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6133.06
# best_prompt_performance: 6133.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001022.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 213.72964695131708  # OPT_PARAM: {"initial": 213.72964695131708, "min": 100, "max": 250, "type": "float"}
    pipeline_weight = 0.6744236788975486  # OPT_PARAM: {"initial": 0.6744236788975486, "min": 0.6, "max": 1.0, "type": "float"}
    demand_buffer = 38.51208791634767  # OPT_PARAM: {"initial": 38.51208791634767, "min": 10, "max": 50, "type": "float"}
    smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.7, "type": "float"}
    variability_factor = 0.8706773921615861  # OPT_PARAM: {"initial": 0.8706773921615861, "min": 0.1, "max": 1.0, "type": "float"}
    min_order = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 30, "type": "int"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate pipeline variability for dynamic buffer
    if pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variability = max(0, avg_pipeline - min(pipeline_orders))
        dynamic_buffer = demand_buffer + variability_factor * pipeline_variability
    else:
        dynamic_buffer = demand_buffer

    # Target inventory level
    target_inventory = base_stock + dynamic_buffer

    # Calculate raw order
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with recent pipeline average
    if pipeline_orders and len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        smoothed_order = smoothing * raw_order + (1 - smoothing) * recent_avg
    else:
        smoothed_order = raw_order

    # Apply minimum order quantity
    if smoothed_order > 0 and smoothed_order < min_order:
        smoothed_order = min_order

    # Ensure integer order
    order_amount = int(round(smoothed_order))

    return order_amount
