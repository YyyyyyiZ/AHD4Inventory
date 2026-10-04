# policy_hash: 1abe2d56ae62e779dd2003c7addbb7153953b0f60692c19c0a078b115b4ac37b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 3841.66
# best_prompt_performance: 3842.87
# best_rel_error_pct: 0.031497
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_013452.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 586.948061724619  # OPT_PARAM: {"initial": 586.948061724619, "min": 400, "max": 800, "type": "float"}
    safety_stock = 80.95043868460192  # OPT_PARAM: {"initial": 80.95043868460192, "min": 80, "max": 200, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 140, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock adjustment
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust safety stock based on lost sales cost ratio
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety_stock

    # Use the maximum of base_stock and target_inventory as order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate base order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with pipeline-aware adjustment
    if len(pipeline_orders) > 0 and order_amount > 0:
        # Weight recent pipeline orders more heavily
        weighted_pipeline = sum(p * (pipeline_weight ** i)
                              for i, p in enumerate(reversed(pipeline_orders)))
        pipeline_avg = weighted_pipeline / sum(pipeline_weight ** i
                                             for i in range(len(pipeline_orders)))

        # Smooth order based on pipeline average
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * pipeline_avg
        order_amount = max(0, smoothed_order)

    return order_amount
