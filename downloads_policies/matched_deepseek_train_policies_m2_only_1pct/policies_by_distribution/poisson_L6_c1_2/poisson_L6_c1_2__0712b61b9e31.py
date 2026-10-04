# policy_hash: 0712b61b9e3168dcf7efdca1fc0d2a076c270ce2be9a472f95548e52fff2e5d1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 2313.34
# best_prompt_performance: 2325.6
# best_rel_error_pct: 0.529970
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251224_051941.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Historical demand data (selling phase only, periods L+1 to L+T)
    historical_demands = [
        93, 117, 98, 89, 106, 101, 80, 107, 103, 101, 109, 98, 110, 103, 107, 128, 93, 104, 92, 86,
        104, 92, 97, 104, 88, 103, 90, 108, 111, 109, 115, 93, 113, 106, 116, 99, 97, 106, 93, 109,
        88, 105, 106, 90, 98, 95, 105, 88, 95, 100
    ]

    # Parameters
    lead_time = 6  # L
    review_period = 1  # OPT_PARAM: {"initial": 1, "min": 1, "max": 10, "type": "int"}
    safety_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 3.0, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 50, "type": "int"}
    max_order = 200  # OPT_PARAM: {"initial": 200, "min": 100, "max": 500, "type": "int"}

    # Demand statistics
    mean_demand = sum(historical_demands) / len(historical_demands)
    # Simple std dev estimation
    variance = sum((d - mean_demand) ** 2 for d in historical_demands) / len(historical_demands)
    std_demand = variance ** 0.5

    # Forecast over lead time + review period
    forecast_horizon = lead_time + review_period
    forecast_demand = mean_demand * forecast_horizon

    # Safety stock
    safety_stock = safety_factor * std_demand * (forecast_horizon ** 0.5)

    # Target inventory position
    target = forecast_demand + safety_stock

    # Current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Order amount
    order_amount = max(min_order, target - inventory_position)
    order_amount = min(max_order, order_amount)

    return order_amount
