# policy_hash: 8913872b925294ee477d39ece3c1879cacbb9dc14e40128179b72ec80e82db2c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 17
# source_prompt_files: 2
# best_target_performance: 6188.0
# best_prompt_performance: 6188.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035425.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.9634550836068  # OPT_PARAM: {"initial": 282.9634550836068, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 67.245026211706  # OPT_PARAM: {"initial": 67.245026211706, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.251907905821862  # OPT_PARAM: {"initial": 0.251907905821862, "min": 0.1, "max": 1.0, "type": "float"}
    demand_forecast = 117.3450262117072  # OPT_PARAM: {"initial": 117.3450262117072, "min": 10, "max": 500, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on demand forecast
    adjusted_base = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0, "max": 1, "type": "float"}

    # Calculate order amount with safety stock consideration
    target_inventory = max(adjusted_base, safety_stock + demand_forecast)
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order

    # Round to integer for practical ordering
    order_amount = int(round(order_amount))

    return order_amount
