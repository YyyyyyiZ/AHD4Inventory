# policy_hash: 69faa363d63b892ca4dd7d1528931e7578247f9595e8bb1fc33b9e7fdaabfe7a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6299.6
# best_prompt_performance: 6299.44
# best_rel_error_pct: 0.002540
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013403.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 450, "type": "float"}
    safety_stock = 88.32696275459138  # OPT_PARAM: {"initial": 88.32696275459138, "min": 80, "max": 200, "type": "float"}
    demand_estimate = 80.8463349873784  # OPT_PARAM: {"initial": 80.8463349873784, "min": 80, "max": 150, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 0.9, "type": "float"}
    adjustment_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    min_order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 30, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate weighted pipeline (more weight on near-term arrivals)
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i)
        weighted_pipeline += order * weight

    # Calculate target inventory level with dynamic adjustment
    base_target = lead_time_demand + safety_stock
    pipeline_adjustment = weighted_pipeline * 0.8
    target_level = max(base_stock, base_target - pipeline_adjustment)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    smoothed_order = raw_order * adjustment_smoothing

    # Apply minimum order threshold
    if smoothed_order < min_order_threshold:
        order_amount = 0
    else:
        order_amount = smoothed_order

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
