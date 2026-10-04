# policy_hash: a0facb5416123609c74202ae0ca218ca1664a1586f02d2d42f0ec8595d1b3aa0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 4739.88
# best_prompt_performance: 4741.34
# best_rel_error_pct: 0.030802
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_004248.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 378.57111440906294  # OPT_PARAM: {"initial": 378.57111440906294, "min": 300, "max": 450, "type": "float"}
    safety_stock = 23.57111440906259  # OPT_PARAM: {"initial": 23.57111440906259, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 110.17436520386545  # OPT_PARAM: {"initial": 110.17436520386545, "min": 90, "max": 130, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    order_smoothing = 0.3513308657746939  # OPT_PARAM: {"initial": 0.3513308657746939, "min": 0.3, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Adjust target based on lost-sales risk (higher p/h ratio)
    target_inventory = base_stock + safety_stock * lost_sales_weight

    # Calculate base order amount with demand forecast adjustment
    base_order = max(0, target_inventory - effective_inventory + demand_forecast)

    # Apply smoothing to reduce order volatility
    smoothed_order = order_smoothing * base_order + (1 - order_smoothing) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
