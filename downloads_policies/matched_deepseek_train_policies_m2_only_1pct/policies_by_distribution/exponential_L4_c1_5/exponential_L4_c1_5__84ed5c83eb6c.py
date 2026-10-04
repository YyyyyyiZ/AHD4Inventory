# policy_hash: 84ed5c83eb6c9c1834b943360d5d0106796c353b07e5845ca15dc68923682875
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 11287.28
# best_prompt_performance: 11287.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_010912.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 319.13860369827347  # OPT_PARAM: {"initial": 319.13860369827347, "min": 200, "max": 600, "type": "float"}
    safety_stock = 60.736994420024324  # OPT_PARAM: {"initial": 60.736994420024324, "min": 50, "max": 300, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    smoothing_factor = 0.0842915138816539  # OPT_PARAM: {"initial": 0.0842915138816539, "min": 0.05, "max": 0.3, "type": "float"}
    lead_time_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand forecast using weighted average of pipeline orders
    if pipeline_orders:
        # Weight recent orders more heavily
        weights = [0.3, 0.4, 0.2, 0.1][:len(pipeline_orders)]
        weights = [w/sum(weights) for w in weights]  # Normalize
        weighted_avg = sum(w * q for w, q in zip(weights, pipeline_orders))
        avg_recent_demand = weighted_avg
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast and lead time
    forecast_adjustment = demand_forecast_factor * avg_recent_demand * lead_time_factor
    adjusted_base_stock = base_stock + forecast_adjustment

    # Dynamic safety stock based on demand variability
    if len(pipeline_orders) >= 2:
        demand_std = (max(pipeline_orders) - min(pipeline_orders)) / 2.0
        dynamic_safety = min(safety_stock * 1.5, safety_stock + 0.3 * demand_std)
    else:
        dynamic_safety = safety_stock

    order_up_to = adjusted_base_stock + dynamic_safety

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with last order
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
    else:
        smoothed_order = raw_order

    # Reasonable order limits
    max_order_limit = 500.0  # OPT_PARAM: {"initial": 500.0, "min": 300, "max": 800, "type": "float"}
    smoothed_order = min(smoothed_order, max_order_limit)

    # Minimum order quantity
    min_order_quantity = 10.1  # OPT_PARAM: {"initial": 10.1, "min": 0, "max": 30, "type": "float"}
    if smoothed_order > 0 and smoothed_order < min_order_quantity:
        smoothed_order = min_order_quantity

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
