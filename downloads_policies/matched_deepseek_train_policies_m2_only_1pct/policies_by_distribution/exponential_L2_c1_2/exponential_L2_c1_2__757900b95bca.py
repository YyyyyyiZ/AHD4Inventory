# policy_hash: 757900b95bca14f060817e18e289598ec41d6d44b347ffc259cdef53f3b47201
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 5899.76
# best_prompt_performance: 5899.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225041.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 219.68296758236585  # OPT_PARAM: {"initial": 219.68296758236585, "min": 180, "max": 300, "type": "float"}
    safety_multiplier = 1.2882249116817668  # OPT_PARAM: {"initial": 1.2882249116817668, "min": 0.9, "max": 1.3, "type": "float"}
    pipeline_coverage = 0.7109739495105192  # OPT_PARAM: {"initial": 0.7109739495105192, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.34005386355583694  # OPT_PARAM: {"initial": 0.34005386355583694, "min": 0.3, "max": 0.8, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5.0, "max": 30.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage

    # Calculate net inventory position (excluding pipeline coverage)
    net_position = on_hand_inventory + effective_pipeline

    # Target inventory position with safety stock
    safety_stock = safety_multiplier * base_stock * 0.3
    target_position = base_stock + safety_stock

    # Calculate order needed
    order_needed = target_position - net_position

    # Apply smoothing
    smoothed_order = order_needed * smoothing_factor

    # Apply minimum order threshold
    if 0 < smoothed_order < min_order_threshold:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
