# policy_hash: 2f4d16edd34076b18e4375ef049bf8fbd825c0340c8645325ee2f8d907d6c55a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6331.24
# best_prompt_performance: 6329.16
# best_rel_error_pct: 0.032853
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235914.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 219.3760682606558  # OPT_PARAM: {"initial": 219.3760682606558, "min": 150, "max": 350, "type": "float"}
    safety_stock = 14.376068260656906  # OPT_PARAM: {"initial": 14.376068260656906, "min": 5, "max": 50, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - effective_inventory)

    # Apply smoothing using weighted average of recent orders
    if pipeline_orders:
        # Give more weight to recent orders
        weights = [0.5, 0.3, 0.15, 0.05][:len(pipeline_orders)]
        weighted_avg = sum(w * o for w, o in zip(weights, pipeline_orders)) / sum(weights[:len(pipeline_orders)])
        order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * weighted_avg
    else:
        order_amount = base_order

    # Apply demand-responsive adjustment
    if pipeline_orders and len(pipeline_orders) >= 2:
        recent_trend = pipeline_orders[0] - pipeline_orders[1]
        adjustment = demand_forecast_factor * recent_trend
        order_amount = max(0, order_amount + adjustment)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
