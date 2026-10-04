# policy_hash: 1105e3ffb6219dea75e0ea469b8d92433998d1263acebfc1cf7df4b31b86485d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 712.34
# best_prompt_performance: 712.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_040118.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 599.6209751777794  # OPT_PARAM: {"initial": 599.6209751777794, "min": 450, "max": 600, "type": "float"}
    safety_stock = 29.999999925242175  # OPT_PARAM: {"initial": 29.999999925242175, "min": 5, "max": 30, "type": "float"}
    demand_forecast = 96.3723181627387  # OPT_PARAM: {"initial": 96.3723181627387, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position with accurate pipeline accounting
    total_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + total_pipeline

    # Target inventory position
    target_position = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing and forecast-based adjustment
    if raw_order > 0:
        # Smooth ordering to avoid large fluctuations
        smoothed_order = raw_order * smoothing_factor + demand_forecast * (1 - smoothing_factor)
        # Cap order based on forecast
        order_amount = min(smoothed_order, demand_forecast * order_multiplier)
    else:
        order_amount = 0

    return order_amount
