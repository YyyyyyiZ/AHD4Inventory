# policy_hash: 67eb83db3c8c3d36f4785463794949bbc092f11c6955a1f3b2746bcc4a5c541b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 6535.6
# best_prompt_performance: 6535.64
# best_rel_error_pct: 0.000612
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052337.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 57.88058244935392  # OPT_PARAM: {"initial": 57.88058244935392, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.999984660142346  # OPT_PARAM: {"initial": 49.999984660142346, "min": 0, "max": 200, "type": "float"}
    demand_forecast_window = 5  # OPT_PARAM: {"initial": 5, "min": 1, "max": 20, "type": "int"}
    forecast_alpha = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.01, "max": 0.99, "type": "float"}
    order_adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast (exponential smoothing placeholder)
    # In practice, this would use historical demand data, but for stationary policy
    # we use a fixed forecast based on typical demand patterns
    typical_demand = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 10, "max": 500, "type": "float"}

    # Calculate expected demand during lead time
    lead_time_demand = typical_demand * len(pipeline_orders)

    # Adjust base stock based on pipeline status
    pipeline_imbalance = max(pipeline_orders) - min(pipeline_orders) if pipeline_orders else 0
    pipeline_factor = 6.0681767225045204  # OPT_PARAM: {"initial": 6.0681767225045204, "min": 5, "max": 50, "type": "float"}

    # Dynamic target inventory level
    dynamic_target = base_stock * pipeline_factor + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, dynamic_target - inventory_position)

    # Apply adjustment factor to be more responsive
    adjusted_order = raw_order * order_adjustment_factor

    # Round to nearest integer (practical constraint)
    order_amount = int(round(adjusted_order))

    return order_amount
