# policy_hash: 49ee2eac040b68abb65037ad4a35db5f45e7316a2ba90128e18249fd5e7ef5fc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6193.06
# best_prompt_performance: 6193.24
# best_rel_error_pct: 0.002906
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234746.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 252.46704339118705  # OPT_PARAM: {"initial": 252.46704339118705, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 19.503588307573775  # OPT_PARAM: {"initial": 19.503588307573775, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 69.50358830757158  # OPT_PARAM: {"initial": 69.50358830757158, "min": 0, "max": 300, "type": "float"}
    pipeline_weight = 1.2046572271481875  # OPT_PARAM: {"initial": 1.2046572271481875, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Adjust base stock based on safety stock and demand buffer
    adjusted_base_stock = base_stock + safety_stock + demand_buffer

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - effective_inventory)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if pipeline_orders:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_past_order

    # Ensure integer order amount
    order_amount = int(round(order_amount))

    return order_amount
