# policy_hash: eacbe30e0fa07e220f6aa2d4a9f8612bff0ea95d07dcf0b98bc849fd7ace7438
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 2
# best_target_performance: 3800.14
# best_prompt_performance: 3798.91
# best_rel_error_pct: 0.032367
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_012321.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 456.84883111710644  # OPT_PARAM: {"initial": 456.84883111710644, "min": 400, "max": 900, "type": "float"}
    safety_stock = 105.2765832829187  # OPT_PARAM: {"initial": 105.2765832829187, "min": 60, "max": 200, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 140, "type": "float"}
    smoothing_factor = 0.18439126782754825  # OPT_PARAM: {"initial": 0.18439126782754825, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    target_inventory = expected_lead_time_demand + safety_stock

    # Adjust base stock based on lost sales cost ratio
    adjusted_base_stock = base_stock * lost_sales_weight

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, target_inventory)

    # Calculate base order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply minimal smoothing only
    if len(pipeline_orders) > 0 and smoothing_factor > 0:
        # Simple weighted pipeline average
        weighted_pipeline = sum(p * (pipeline_weight ** i)
                              for i, p in enumerate(reversed(pipeline_orders)))
        pipeline_avg = weighted_pipeline / sum(pipeline_weight ** i
                                             for i in range(len(pipeline_orders)))

        # Very light smoothing to reduce volatility
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * pipeline_avg
        order_amount = max(0, smoothed_order)

    return order_amount
