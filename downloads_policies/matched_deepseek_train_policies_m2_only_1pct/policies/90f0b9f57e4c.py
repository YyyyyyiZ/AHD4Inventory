# policy_hash: 90f0b9f57e4cbb71afb38cc4fa1efbf90284b5014fc1731315f7808b306caa7d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 2
# best_target_performance: 6102.88
# best_prompt_performance: 6102.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054229.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 422.0717433251398  # OPT_PARAM: {"initial": 422.0717433251398, "min": 300, "max": 550, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    safety_stock = 82.07174332514045  # OPT_PARAM: {"initial": 82.07174332514045, "min": 50, "max": 120, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate effective pipeline (full weight for accurate position)
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Estimate upcoming demand from pipeline arrivals (next L periods)
    upcoming_demand_estimate = sum(pipeline_orders) * demand_forecast_factor

    # Dynamic target level adjusts for expected demand
    dynamic_target = base_stock + safety_stock + upcoming_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply smoothing only when order is substantial
    if raw_order > base_stock * 0.1:  # Only smooth larger orders
        order_amount = smoothing_factor * raw_order
    else:
        order_amount = raw_order  # No smoothing for small adjustments

    # Round to nearest integer
    return order_amount
