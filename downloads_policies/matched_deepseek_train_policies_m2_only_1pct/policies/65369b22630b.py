# policy_hash: 65369b22630b58bfe9a17efb3dd66735a21caf0b8408330e02fd8e3a7e9aeac2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 6180.52
# best_prompt_performance: 6179.92
# best_rel_error_pct: 0.009708
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013902.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 300, "max": 500, "type": "float"}
    safety_stock = 115.68710685909186  # OPT_PARAM: {"initial": 115.68710685909186, "min": 100, "max": 200, "type": "float"}
    demand_estimate = 93.64465708566169  # OPT_PARAM: {"initial": 93.64465708566169, "min": 90, "max": 150, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    adjustment_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with lost-sales adjustment
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time * lost_sales_weight

    # Calculate weighted pipeline (more weight on near-term arrivals)
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (lead_time - i - 1)
        weighted_pipeline += order * weight

    # Calculate target inventory level
    base_target = lead_time_demand + safety_stock
    pipeline_adjustment = weighted_pipeline * 0.7
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
