# policy_hash: f5de3cf9672342232023bb354e8279b9c5ca120a2ebf4809662dc8eacf7bab83
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6190.6
# best_prompt_performance: 6191.44
# best_rel_error_pct: 0.013569
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040103.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 184.39601533204493  # OPT_PARAM: {"initial": 184.39601533204493, "min": 50, "max": 400, "type": "float"}
    safety_stock = 49.39601533204463  # OPT_PARAM: {"initial": 49.39601533204463, "min": 10, "max": 150, "type": "float"}
    demand_forecast_factor = 1.2803872088937387  # OPT_PARAM: {"initial": 1.2803872088937387, "min": 0.3, "max": 1.5, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 0.2382216916076452  # OPT_PARAM: {"initial": 0.2382216916076452, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline for demand forecasting
    # Weight recent pipeline orders more heavily
    weighted_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders[:3]):  # Look at next 3 arrivals
        weight = pipeline_weight ** i
        weighted_pipeline += order * weight
        total_weight += weight

    avg_weighted_demand = weighted_pipeline / total_weight if total_weight > 0 else 0

    # Adjust base stock based on weighted demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_weighted_demand

    # Calculate target inventory position with safety stock
    target_position = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing using last order placed
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
