# policy_hash: 3c6cc211c5288c544cc3830ed781dc46d80258989b3167bf01c7ed41cfd0deeb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 10807.09
# best_prompt_performance: 10806.99
# best_rel_error_pct: 0.000925
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072135.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 317.69663047919164  # OPT_PARAM: {"initial": 317.69663047919164, "min": 100, "max": 600, "type": "float"}
    safety_stock = 35.42538027161113  # OPT_PARAM: {"initial": 35.42538027161113, "min": 10, "max": 150, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 3.0, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline orders as demand signal (they reflect past decisions)
    # Weight recent pipeline orders more heavily
    weighted_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight
        total_weight += weight

    avg_pipeline_demand = weighted_pipeline / total_weight if total_weight > 0 else 0

    # Forecast demand using pipeline information
    forecast_demand = avg_pipeline_demand * demand_forecast_factor

    # Dynamic target based on forecast and safety stock
    target_inventory = max(base_stock, safety_stock + forecast_demand * 2)

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    return order_amount
