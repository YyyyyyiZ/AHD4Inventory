# policy_hash: 43ccfaa78244cbb74dde44cf5f22c7b69aa1d7b4982cc5b6e1d303b3148521b6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 11279.5
# best_prompt_performance: 11279.34
# best_rel_error_pct: 0.001419
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005542.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 347.337258024579  # OPT_PARAM: {"initial": 347.337258024579, "min": 100, "max": 800, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 200, "type": "float"}
    demand_forecast_factor = 0.48175699064355904  # OPT_PARAM: {"initial": 0.48175699064355904, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.9533506910348422  # OPT_PARAM: {"initial": 0.9533506910348422, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    effective_pipeline = pipeline_weight * sum(pipeline_orders[:2]) + (1 - pipeline_weight) * sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    adjusted_base_stock = base_stock + demand_forecast_factor * effective_pipeline

    # Ensure minimum safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing using last order if available
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
