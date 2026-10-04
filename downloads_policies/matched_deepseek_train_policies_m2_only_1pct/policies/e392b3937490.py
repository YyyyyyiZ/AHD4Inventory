# policy_hash: e392b393749082055c6e1acf95f9dd75675472e7290564da84085a1988b3fae3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 43
# source_prompt_files: 1
# best_target_performance: 3776.76
# best_prompt_performance: 3775.09
# best_rel_error_pct: 0.044218
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_013014.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 486.60995178097374  # OPT_PARAM: {"initial": 486.60995178097374, "min": 400, "max": 900, "type": "float"}
    safety_stock = 106.55821667051192  # OPT_PARAM: {"initial": 106.55821667051192, "min": 60, "max": 200, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 140, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock
    expected_lead_time_demand = demand_forecast * lead_time
    target_inventory = expected_lead_time_demand + safety_stock

    # Adjust base stock based on lost sales cost ratio
    adjusted_base_stock = base_stock * lost_sales_weight

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, target_inventory)

    # Calculate base order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with pipeline consideration
    if lead_time > 0 and smoothing_factor > 0:
        # Weighted pipeline average (recent orders weighted more heavily)
        weighted_pipeline = sum(p * (pipeline_weight ** i)
                              for i, p in enumerate(reversed(pipeline_orders)))
        pipeline_avg = weighted_pipeline / sum(pipeline_weight ** i
                                             for i in range(lead_time))

        # Smooth order to reduce volatility while maintaining responsiveness
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * pipeline_avg
        order_amount = max(0, smoothed_order)

    return order_amount
