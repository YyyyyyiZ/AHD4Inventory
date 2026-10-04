# policy_hash: b238c5d589de09d72d690135190c0a163dd962f02eae26720ce5c8ce9007523a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6107.28
# best_prompt_performance: 6107.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054220.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 447.6440211488849  # OPT_PARAM: {"initial": 447.6440211488849, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.8097539318634184  # OPT_PARAM: {"initial": 0.8097539318634184, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 1.0, "type": "float"}
    safety_stock = 77.64402114888712  # OPT_PARAM: {"initial": 77.64402114888712, "min": 30, "max": 150, "type": "float"}
    demand_forecast_factor = 0.30689024831329736  # OPT_PARAM: {"initial": 0.30689024831329736, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate effective pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on recent pipeline pattern (demand forecast)
    recent_pipeline_avg = sum(pipeline_orders[:3]) / 3 if len(pipeline_orders) >= 3 else 0
    adjusted_base = base_stock + demand_forecast_factor * recent_pipeline_avg

    # Calculate target inventory level
    target_level = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_level - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
