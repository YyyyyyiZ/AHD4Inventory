# policy_hash: 83b290ad525af36ac98cf99247cf8510d8277612cb2701d973178aa2076ffa89
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3298.3
# best_prompt_performance: 3298.37
# best_rel_error_pct: 0.002122
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_084801.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 624.8503726806324  # OPT_PARAM: {"initial": 624.8503726806324, "min": 500, "max": 900, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    order_threshold = 20.200000000000003  # OPT_PARAM: {"initial": 20.200000000000003, "min": 5, "max": 40, "type": "float"}
    safety_stock = 75.15177295457154  # OPT_PARAM: {"initial": 75.15177295457154, "min": 50, "max": 200, "type": "float"}
    demand_adjustment = 0.9677473029674118  # OPT_PARAM: {"initial": 0.9677473029674118, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_lookback = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    pipeline_threshold = 200  # OPT_PARAM: {"initial": 200, "min": 100, "max": 400, "type": "int"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on recent pipeline pattern
    recent_pipeline = sum(pipeline_orders[:pipeline_lookback]) if len(pipeline_orders) >= pipeline_lookback else sum(pipeline_orders)
    if recent_pipeline < pipeline_threshold:
        adjusted_base_stock = base_stock * demand_adjustment
    else:
        adjusted_base_stock = base_stock

    # Add safety stock component
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply ordering threshold
    if order_amount < order_threshold:
        order_amount = 0

    return order_amount
