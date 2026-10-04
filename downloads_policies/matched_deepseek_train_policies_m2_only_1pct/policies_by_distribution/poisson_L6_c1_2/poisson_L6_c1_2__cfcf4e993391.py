# policy_hash: cfcf4e993391add9d80e67ef2fe70c5f7fca295cdb59ad3d0537d26927b4251b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2196.24
# best_prompt_performance: 2199.71
# best_rel_error_pct: 0.157997
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251224_052245.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Historical demand data (selling phase only, periods L+1 to L+T)
    historical_demands = [
        93, 117, 98, 89, 106, 101, 80, 107, 103, 101, 109, 98, 110, 103, 107, 128, 93, 104, 92, 86,
        104, 92, 97, 104, 88, 103, 90, 108, 111, 109, 115, 93, 113, 106, 116, 99, 97, 106, 93, 109,
        88, 105, 106, 90, 98, 95, 105, 88, 95, 100
    ]

    # Parameters
    lead_time = 6  # L
    safety_factor = 2.6764515704510545  # OPT_PARAM: {"initial": 2.6764515704510545, "min": 0.5, "max": 3.0, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 20, "type": "int"}
    max_order = 250  # OPT_PARAM: {"initial": 250, "min": 150, "max": 400, "type": "int"}

    # Demand statistics
    mean_demand = sum(historical_demands) / len(historical_demands)

    # Calculate standard deviation
    variance = sum((d - mean_demand) ** 2 for d in historical_demands) / len(historical_demands)
    std_demand = variance ** 0.5

    # Target inventory position = mean demand over lead time + safety stock
    forecast_demand = mean_demand * lead_time
    safety_stock = safety_factor * std_demand * (lead_time ** 0.5)
    target = forecast_demand + safety_stock

    # Current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Order amount
    order_amount = max(min_order, target - inventory_position)
    order_amount = min(max_order, order_amount)

    return order_amount
