# policy_hash: afc9f0117b7eec3d4e43015b561554072961524cdcafdbbff270fac1146b29a0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 65
# source_prompt_files: 1
# best_target_performance: 2279.7
# best_prompt_performance: 2279.84
# best_rel_error_pct: 0.006141
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_013209.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 503.90373375468954  # OPT_PARAM: {"initial": 503.90373375468954, "min": 400, "max": 900, "type": "float"}
    safety_stock = 20.3904452327293  # OPT_PARAM: {"initial": 20.3904452327293, "min": 10, "max": 80, "type": "float"}
    demand_forecast_factor = 0.12402853190988798  # OPT_PARAM: {"initial": 0.12402853190988798, "min": 0.05, "max": 0.5, "type": "float"}
    smoothing_factor = 0.17947025435000988  # OPT_PARAM: {"initial": 0.17947025435000988, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time_days = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using weighted average of recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use last 4 periods with more weight on recent orders
        recent_orders = pipeline_orders[-4:] if len(pipeline_orders) >= 4 else pipeline_orders
        weights = [0.1, 0.2, 0.3, 0.4][-len(recent_orders):]
        weighted_sum = sum(w * o for w, o in zip(weights, recent_orders))
        forecast_demand = weighted_sum * demand_forecast_factor * lead_time_days
    else:
        forecast_demand = 0

    # Dynamic target inventory based on lead time and forecast
    target_inventory = base_stock + safety_stock + forecast_demand

    # Calculate raw order amount with lead time adjustment
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with weighted historical orders
    if len(pipeline_orders) > 0:
        # Use exponential weighting for past orders
        weights = [0.5 ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]
        weighted_avg = sum(w * o for w, o in zip(weights, pipeline_orders))
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * weighted_avg
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
