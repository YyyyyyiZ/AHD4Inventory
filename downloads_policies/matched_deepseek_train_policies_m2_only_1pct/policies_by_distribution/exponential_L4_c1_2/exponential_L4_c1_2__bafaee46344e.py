# policy_hash: bafaee46344e948806c42065b6c50a1911bcba1b057cdf4a7dd29bcf8cb8f557
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6133.16
# best_prompt_performance: 6133.16
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001635.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 195.39999999999998  # OPT_PARAM: {"initial": 195.39999999999998, "min": 150, "max": 220, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 30, "max": 60, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 20, "type": "int"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + weighted_pipeline

    # Target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate base order
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    if pipeline_orders and len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]
        recent_avg = sum(recent_orders) / 2
        smoothed_order = smoothing_factor * base_order + (1 - smoothing_factor) * recent_avg
    else:
        smoothed_order = base_order

    # Apply minimum order quantity
    if smoothed_order > 0 and smoothed_order < min_order:
        smoothed_order = min_order

    # Ensure integer order
    order_amount = int(round(smoothed_order))

    return order_amount
