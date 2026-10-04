# policy_hash: 666c517e58d4492db925c7329a1df38692d2c7436b0fab523e473ceb69e4dfc8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 7177.57
# best_prompt_performance: 7177.57
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012203.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 418.0182266985495  # OPT_PARAM: {"initial": 418.0182266985495, "min": 100, "max": 800, "type": "float"}
    safety_stock = 180.0  # OPT_PARAM: {"initial": 180.0, "min": 50, "max": 400, "type": "float"}
    demand_forecast = 109.89411391962548  # OPT_PARAM: {"initial": 109.89411391962548, "min": 50, "max": 300, "type": "float"}
    smoothing_factor = 0.32149230747084157  # OPT_PARAM: {"initial": 0.32149230747084157, "min": 0.01, "max": 0.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline to account for future arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                          for i, p in enumerate(reversed(pipeline_orders)))

    # Adjust base stock based on recent demand pattern
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    if recent_arrivals > 0:
        demand_deviation = recent_arrivals - demand_forecast
        adjustment = demand_deviation * smoothing_factor
        adjusted_base = base_stock + adjustment
    else:
        adjusted_base = base_stock

    # Combine base stock with weighted pipeline consideration
    effective_target = max(adjusted_base, safety_stock + 0.3 * weighted_pipeline)

    # Calculate order amount with smoother adjustment
    order_amount = max(0, effective_target - inventory_position)

    # Round to nearest integer (orders are discrete)
    return order_amount
