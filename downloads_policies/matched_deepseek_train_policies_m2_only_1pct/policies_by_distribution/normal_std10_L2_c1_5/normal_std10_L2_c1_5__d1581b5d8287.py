# policy_hash: d1581b5d82878163f4a99b29c0a6606451a5eedbaf8a78194dba1e3eaa191619
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1147.95
# best_prompt_performance: 1141.94
# best_rel_error_pct: 0.523542
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_101145.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 444.6869246923494  # OPT_PARAM: {"initial": 444.6869246923494, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 0.8137172488095729  # OPT_PARAM: {"initial": 0.8137172488095729, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2769887934851367  # OPT_PARAM: {"initial": 0.2769887934851367, "min": 0.2, "max": 0.4, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 10, "type": "int"}
    safety_stock = 22.85853642432338  # OPT_PARAM: {"initial": 22.85853642432338, "min": 10, "max": 50, "type": "float"}
    demand_anticipation = 0.27106598165692813  # OPT_PARAM: {"initial": 0.27106598165692813, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple base stock policy with safety stock
    target_inventory = base_stock + safety_stock
    raw_order = target_inventory - inventory_position

    # Apply demand anticipation based on pipeline
    if sum(pipeline_orders) > 0:
        raw_order = raw_order * (1 + demand_anticipation)

    # Ensure non-negative order
    order_amount = max(min_order, raw_order)

    # Apply smoothing to reduce order volatility
    if order_amount > min_order:
        smoothed_order = smoothing_factor * order_amount
        order_amount = max(min_order, smoothed_order)

    return order_amount
