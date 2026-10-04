# policy_hash: cc89adc27d0a539cb099b79e98d8a1478d97d31192625685fea11fdf2f52f528
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 11028.54
# best_prompt_performance: 11028.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_085611.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 494.59999999998456  # OPT_PARAM: {"initial": 494.59999999998456, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 130.39999999998625  # OPT_PARAM: {"initial": 130.39999999998625, "min": 50, "max": 250, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic safety stock adjustment based on pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_std = (max(pipeline_orders) - min(pipeline_orders)) / 2.0
        dynamic_safety = safety_stock * (1.0 + min(0.5, pipeline_std / 200.0))
    else:
        dynamic_safety = safety_stock

    # Adjust base stock based on lost sales cost ratio
    adjusted_base_stock = base_stock + dynamic_safety * lost_sales_weight

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with consistent factor
    order_amount = smoothing_factor * order_up_to

    # Ensure minimum order size for efficiency
    if order_amount > 0 and order_amount < 10:
        order_amount = 10

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
