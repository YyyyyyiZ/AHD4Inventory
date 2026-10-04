# policy_hash: 6ce337b358572c74a22672c50dbb40c6aeda2bfc14f01f6ce91045a5d597be3f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 22
# source_prompt_files: 2
# best_target_performance: 10971.6
# best_prompt_performance: 10971.6
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090032.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 542.4034874351124  # OPT_PARAM: {"initial": 542.4034874351124, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.6, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 30, "max": 150, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate base order amount
    order_amount = max(0, base_stock - inventory_position)

    # Add safety stock adjustment based on recent pipeline variability
    if len(pipeline_orders) >= 2:
        recent_avg = sum(pipeline_orders[-2:]) / 2
        if recent_avg > 150:  # High recent orders indicate potential high demand
            order_amount += safety_stock

    # Apply smoothing
    order_amount = smoothing_factor * order_amount

    # Round to nearest integer (orders should be discrete units)
    order_amount = int(round(order_amount))

    return order_amount
