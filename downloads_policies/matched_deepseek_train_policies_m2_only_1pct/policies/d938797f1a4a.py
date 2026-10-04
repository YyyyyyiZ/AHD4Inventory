# policy_hash: d938797f1a4adea6b4954653afa9821cbf3e7766cfcf9a0c570472312ab4a32c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 14087.26
# best_prompt_performance: 14087.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055848.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 553.7875397347028  # OPT_PARAM: {"initial": 553.7875397347028, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 149.80000000058186  # OPT_PARAM: {"initial": 149.80000000058186, "min": 50, "max": 300, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline orders
    # (pipeline orders reflect past demand patterns)
    if len(pipeline_orders) >= 3:
        recent_orders = pipeline_orders[-3:]  # Last 3 orders placed
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
        forecast_adjustment = avg_recent_demand * demand_forecast_factor
    else:
        forecast_adjustment = 0

    # Dynamic base stock level
    dynamic_base_stock = base_stock + safety_stock + forecast_adjustment

    # Calculate order amount with smoothing
    raw_order = max(0, dynamic_base_stock - inventory_position)

    # Round to nearest integer (as required by output type)
    order_amount = int(round(raw_order))

    return order_amount
