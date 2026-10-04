# policy_hash: 9613d6b09c93b0cbd64d0f833d9e0ca89745764bbcc76073b00c37b5b62b8d59
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2135.84
# best_prompt_performance: 2141.05
# best_rel_error_pct: 0.243932
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_085823.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 610.242481293283  # OPT_PARAM: {"initial": 610.242481293283, "min": 500, "max": 900, "type": "float"}
    pipeline_weight = 0.9494800187812196  # OPT_PARAM: {"initial": 0.9494800187812196, "min": 0.7, "max": 1.0, "type": "float"}
    order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}
    safety_stock = 85.07494914127362  # OPT_PARAM: {"initial": 85.07494914127362, "min": 50, "max": 200, "type": "float"}
    demand_adjustment = 0.9505199812187805  # OPT_PARAM: {"initial": 0.9505199812187805, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_lookback = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 6, "type": "int"}
    pipeline_threshold = 180  # OPT_PARAM: {"initial": 180, "min": 100, "max": 400, "type": "int"}
    max_order = 150  # OPT_PARAM: {"initial": 150, "min": 100, "max": 300, "type": "int"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on recent pipeline pattern
    recent_pipeline = sum(pipeline_orders[:pipeline_lookback]) if len(pipeline_orders) >= pipeline_lookback else sum(pipeline_orders)
    if recent_pipeline < pipeline_threshold:
        adjusted_base_stock = base_stock * demand_adjustment
    else:
        adjusted_base_stock = base_stock * 0.95

    # Add safety stock component
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply maximum order limit
    order_amount = min(order_amount, max_order)

    # Apply ordering threshold
    if order_amount < order_threshold:
        order_amount = 0

    return order_amount
