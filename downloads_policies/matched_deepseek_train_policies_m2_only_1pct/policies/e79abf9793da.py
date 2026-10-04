# policy_hash: e79abf9793dae703ce1fdeba6bbdf52ec86418288a7995f9f4c68684884f51b3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 12083.5
# best_prompt_performance: 12082.66
# best_rel_error_pct: 0.006952
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002802.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 448.99993377977387  # OPT_PARAM: {"initial": 448.99993377977387, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 0, "max": 500, "type": "float"}
    demand_buffer = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders) if pipeline_orders else 0
    pipeline_factor = min(1.5, 1.0 + pipeline_variance / 10000.0)  # OPT_PARAM: {"initial": 10000.0, "min": 1000, "max": 50000, "type": "float"}

    # Dynamic target based on safety stock and demand buffer
    dynamic_target = base_stock * pipeline_factor + safety_stock + demand_buffer

    # Calculate order amount with smoothing
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}
    if pipeline_orders:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * avg_past_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer (as required by output type)
    order_amount = int(round(smoothed_order))

    return order_amount
