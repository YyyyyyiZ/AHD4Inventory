# policy_hash: 15084c0f3631b67ac7ed68497356fdeb3fb2543c78fc1ac16607e97b1181ff0b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1261.8
# best_prompt_performance: 1271.26
# best_rel_error_pct: 0.749723
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_150506.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 407.1627656963218  # OPT_PARAM: {"initial": 407.1627656963218, "min": 350, "max": 500, "type": "float"}
    safety_stock = 34.717524882322195  # OPT_PARAM: {"initial": 34.717524882322195, "min": 20, "max": 60, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    variability_buffer = 19.02880700859306  # OPT_PARAM: {"initial": 19.02880700859306, "min": 0, "max": 30, "type": "float"}
    lost_sales_weight = 2.644092645521113  # OPT_PARAM: {"initial": 2.644092645521113, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Demand forecast based on pipeline average with adjustment
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        demand_adjustment = demand_forecast_factor * avg_pipeline
    else:
        demand_adjustment = 0

    # Adjust for pipeline variability
    if len(pipeline_orders) > 1:
        pipeline_variability = max(pipeline_orders) - min(pipeline_orders)
    else:
        pipeline_variability = 0

    pipeline_effect = pipeline_weight * pipeline_variability

    # Dynamic target with stronger emphasis on preventing lost sales
    target_inventory = (base_stock + safety_stock - pipeline_effect +
                       demand_adjustment + variability_buffer * lost_sales_weight)

    # Calculate order with smoothing
    raw_order = target_inventory - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
