# policy_hash: 051a816a2a9ed207e3c7b9ab4092d252bfdb4c73fca66fbe97d1101bb9c85488
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3760.76
# best_prompt_performance: 3723.4
# best_rel_error_pct: 0.993416
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251219_115111.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 588.6808472543422  # OPT_PARAM: {"initial": 588.6808472543422, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.4729971041938981  # OPT_PARAM: {"initial": 0.4729971041938981, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline distribution
    near_term_pipeline = sum(pipeline_orders[:2])  # Orders arriving in next 2 periods
    far_term_pipeline = sum(pipeline_orders[2:])   # Orders arriving later

    # Dynamic target: reduce target when near-term pipeline is high
    adjusted_base = base_stock - pipeline_weight * near_term_pipeline

    # Add safety stock component
    target_inventory = max(safety_stock, adjusted_base)

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand forecast adjustment (smooth ordering)
    forecast_adjustment = demand_forecast_factor * raw_order

    # Round to nearest integer (as required by output type)
    order_amount = int(round(forecast_adjustment))

    return order_amount
