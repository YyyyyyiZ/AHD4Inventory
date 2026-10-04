# policy_hash: 6b687eb0ef64517c71098f37f0bae6272eb94e60d4fb66f3a447afff0efe39df
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 3919.14
# best_prompt_performance: 3918.66
# best_rel_error_pct: 0.012248
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_005239.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 250, "max": 400, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 130, "type": "float"}
    pipeline_coverage_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    demand_variability_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 10, "max": 50, "type": "float"}
    max_order_cap = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 150, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Calculate safety stock with demand variability
    safety_stock = safety_stock_factor * demand_forecast * (1 + demand_variability_factor)

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Adjust for pipeline coverage - less aggressive adjustment
    if expected_demand_during_lead_time > 0:
        pipeline_coverage = sum(pipeline_orders) / expected_demand_during_lead_time
        adjustment = pipeline_coverage_factor * min(1.0, pipeline_coverage)
        adjusted_target = target_inventory_position * (1 - adjustment)
    else:
        adjusted_target = target_inventory_position

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing with more weight to current gap
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Apply minimum order threshold and maximum cap
    if order_amount < min_order_threshold:
        order_amount = 0
    else:
        order_amount = min(order_amount, max_order_cap)

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
