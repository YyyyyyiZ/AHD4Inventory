# policy_hash: bd5d2ad91574964c6edf9d8c011d68f8bab1ef8b41f93184e2b7edd4abb7262d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 11126.28
# best_prompt_performance: 11126.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_085206.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 572.733755148265  # OPT_PARAM: {"initial": 572.733755148265, "min": 400, "max": 800, "type": "float"}
    pipeline_weight = 0.9018822198749741  # OPT_PARAM: {"initial": 0.9018822198749741, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2940233122725106  # OPT_PARAM: {"initial": 0.2940233122725106, "min": 0.2, "max": 0.6, "type": "float"}
    safety_stock = 59.10191848083344  # OPT_PARAM: {"initial": 59.10191848083344, "min": 20, "max": 120, "type": "float"}
    demand_anticipation_factor = 1.1211221089548569  # OPT_PARAM: {"initial": 1.1211221089548569, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate base order amount
    order_amount = max(0, base_stock - inventory_position)

    # Adjust for anticipated demand based on recent pipeline
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        if recent_avg > 100:  # Moderate threshold for demand anticipation
            order_amount *= demand_anticipation_factor

    # Add safety stock based on pipeline variability
    if len(pipeline_orders) >= 3:
        pipeline_std = (max(pipeline_orders) - min(pipeline_orders)) / 2
        if pipeline_std > 50:
            order_amount += safety_stock

    # Apply smoothing to reduce order volatility
    order_amount = smoothing_factor * order_amount

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
