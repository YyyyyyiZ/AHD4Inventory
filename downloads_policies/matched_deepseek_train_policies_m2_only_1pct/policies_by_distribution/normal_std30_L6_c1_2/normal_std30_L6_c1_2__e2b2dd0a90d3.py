# policy_hash: e2b2dd0a90d3eae0873feee0c4a836fe8785ad8b56fc6bf967c534c421303a2d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2253.06
# best_prompt_performance: 2253.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_060907.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 380, "max": 480, "type": "float"}
    safety_stock = 65.0  # OPT_PARAM: {"initial": 65.0, "min": 40, "max": 90, "type": "float"}
    demand_forecast = 85.01598778210753  # OPT_PARAM: {"initial": 85.01598778210753, "min": 85, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.46193540218131696  # OPT_PARAM: {"initial": 0.46193540218131696, "min": 0.4, "max": 0.9, "type": "float"}
    threshold_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    variability_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 4, "max": 8, "type": "int"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 30, "type": "float"}

    # Calculate effective lead time demand
    effective_lead_time = min(lead_time, len(pipeline_orders))
    expected_lead_time_demand = demand_forecast * effective_lead_time

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                           for i, p in enumerate(reversed(pipeline_orders[:effective_lead_time])))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) > 0:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((p - pipeline_mean) ** 2 for p in pipeline_orders)
                        / len(pipeline_orders)) ** 0.5
        adjusted_safety = safety_stock + variability_factor * pipeline_std
    else:
        adjusted_safety = safety_stock

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety

    # Apply base_stock cap
    order_up_to = min(base_stock, target_inventory)

    # Calculate order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with minimum order threshold
    if raw_order > demand_forecast * threshold_factor:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = raw_order

    # Apply minimum order quantity
    order_amount = max(min_order, order_amount)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
