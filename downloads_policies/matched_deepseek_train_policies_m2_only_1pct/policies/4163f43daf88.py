# policy_hash: 4163f43daf88e7200f847e45114360c0859079c3838a0784358b43c304257c94
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 6650.75
# best_prompt_performance: 6640.96
# best_rel_error_pct: 0.147201
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035029.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 264.1481824875687  # OPT_PARAM: {"initial": 264.1481824875687, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 42.49482609106617  # OPT_PARAM: {"initial": 42.49482609106617, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.9367675539666099  # OPT_PARAM: {"initial": 0.9367675539666099, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + pipeline_orders[0]

    # Calculate weighted pipeline for future arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Adjust base stock based on pipeline status
    adjusted_base = base_stock + safety_stock * (1 - pipeline_weight)

    # Calculate order amount with pipeline consideration
    order_amount = max(0, adjusted_base - effective_inventory - weighted_pipeline)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.15230435670159917  # OPT_PARAM: {"initial": 0.15230435670159917, "min": 0.1, "max": 1.0, "type": "float"}
    if hasattr(compute_order_amount, '_last_order'):
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * compute_order_amount._last_order

    compute_order_amount._last_order = order_amount
    return order_amount
