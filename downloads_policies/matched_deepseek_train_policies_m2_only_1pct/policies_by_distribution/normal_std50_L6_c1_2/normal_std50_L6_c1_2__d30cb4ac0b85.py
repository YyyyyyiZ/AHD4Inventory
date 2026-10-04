# policy_hash: d30cb4ac0b856f20d969cecc41bb8b607e3cea310c857df9b2f4ae6c47c96015
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 3903.98
# best_prompt_performance: 3904.12
# best_rel_error_pct: 0.003586
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_010256.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 227.20000000001573  # OPT_PARAM: {"initial": 227.20000000001573, "min": 200, "max": 350, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 130, "type": "float"}
    pipeline_coverage_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    min_order_multiplier = 0.1311660660414577  # OPT_PARAM: {"initial": 0.1311660660414577, "min": 0.05, "max": 0.3, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    demand_variability_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with variability adjustment
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time * demand_variability_factor

    # Dynamic safety stock with improved formula
    safety_stock = safety_stock_factor * demand_forecast * (lost_sales_weight / 1.5)

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Adjust for pipeline coverage with weighted approach
    if expected_demand_during_lead_time > 0:
        pipeline_coverage = sum(pipeline_orders) / expected_demand_during_lead_time
        # Use pipeline_weight to balance pipeline consideration
        adjustment = pipeline_coverage_factor * min(1.0, pipeline_coverage) * pipeline_weight
        adjusted_target = target_inventory_position * (1 - adjustment)
    else:
        adjusted_target = target_inventory_position

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Apply minimum order threshold
    min_order = min_order_multiplier * demand_forecast
    if base_order > 0 and base_order < min_order:
        base_order = min_order

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
