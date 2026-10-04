# policy_hash: d76c26387082f255f1870c0f901661259010f07d6e256b2230b034620a48dd98
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 3766.89
# best_prompt_performance: 3766.22
# best_rel_error_pct: 0.017787
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_014608.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 447.55433286332175  # OPT_PARAM: {"initial": 447.55433286332175, "min": 400, "max": 900, "type": "float"}
    safety_stock = 105.27659451465904  # OPT_PARAM: {"initial": 105.27659451465904, "min": 60, "max": 200, "type": "float"}
    demand_forecast = 90.00005329572623  # OPT_PARAM: {"initial": 90.00005329572623, "min": 90, "max": 140, "type": "float"}
    smoothing_factor = 0.14804413962850962  # OPT_PARAM: {"initial": 0.14804413962850962, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.20039853342359  # OPT_PARAM: {"initial": 1.20039853342359, "min": 1.2, "max": 2.5, "type": "float"}
    holding_weight = 1.0160973713879222  # OPT_PARAM: {"initial": 1.0160973713879222, "min": 0.5, "max": 1.5, "type": "float"}
    lead_time_adjustment = 0.9520419386599032  # OPT_PARAM: {"initial": 0.9520419386599032, "min": 0.8, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety stock
    expected_lead_time_demand = demand_forecast * len(pipeline_orders) * lead_time_adjustment
    target_inventory = expected_lead_time_demand + safety_stock

    # Adjust base stock based on cost ratio (balance holding vs lost sales)
    adjusted_base_stock = base_stock * (lost_sales_weight / holding_weight)

    # Calculate order-up-to level
    order_up_to = max(adjusted_base_stock, target_inventory)

    # Calculate base order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with pipeline consideration
    if len(pipeline_orders) > 0 and smoothing_factor > 0:
        # Weighted pipeline average (recent orders get more weight)
        weighted_pipeline = sum(p * (pipeline_weight ** i)
                              for i, p in enumerate(reversed(pipeline_orders)))
        pipeline_avg = weighted_pipeline / sum(pipeline_weight ** i
                                             for i in range(len(pipeline_orders)))

        # Smooth order to reduce volatility while maintaining responsiveness
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * pipeline_avg
        order_amount = max(0, smoothed_order)

    return order_amount
