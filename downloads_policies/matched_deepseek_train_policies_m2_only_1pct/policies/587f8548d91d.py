# policy_hash: 587f8548d91da4b3d51297c4ea105852e91608743a39363c7d07e9f7cf6f98c4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3913.24
# best_prompt_performance: 3912.96
# best_rel_error_pct: 0.007155
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_005023.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 284.99999999996965  # OPT_PARAM: {"initial": 284.99999999996965, "min": 200, "max": 350, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 140, "type": "float"}
    pipeline_coverage_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    min_order_multiplier = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Add safety stock based on demand variability
    safety_stock = safety_stock_factor * demand_forecast

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Adjust for pipeline coverage
    if expected_demand_during_lead_time > 0:
        pipeline_coverage = sum(pipeline_orders) / expected_demand_during_lead_time
        adjustment = pipeline_coverage_factor * min(1.0, pipeline_coverage)
        adjusted_target = target_inventory_position * (1 - adjustment)
    else:
        adjusted_target = target_inventory_position

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Apply minimum order threshold based on demand forecast
    min_order = min_order_multiplier * demand_forecast
    if base_order > 0 and base_order < min_order:
        base_order = min_order

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
