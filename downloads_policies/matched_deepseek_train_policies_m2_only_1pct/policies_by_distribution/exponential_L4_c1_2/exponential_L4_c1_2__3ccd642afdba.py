# policy_hash: 3ccd642afdba8c416aa6d0da56146a693622e3855969b3f86a8577291faedf2e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 54
# source_prompt_files: 1
# best_target_performance: 6103.12
# best_prompt_performance: 6103.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002134.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 209.68947627149132  # OPT_PARAM: {"initial": 209.68947627149132, "min": 100, "max": 300, "type": "float"}
    safety_stock = 45.73297555486707  # OPT_PARAM: {"initial": 45.73297555486707, "min": 10, "max": 60, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.20591257045138056  # OPT_PARAM: {"initial": 0.20591257045138056, "min": 0.1, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - effective_inventory)

    # Apply smoothing using weighted average of recent orders
    if pipeline_orders:
        # Exponential weighting for recent orders
        weights = [0.6, 0.25, 0.1, 0.05][:len(pipeline_orders)]
        weighted_avg = sum(w * o for w, o in zip(weights, pipeline_orders)) / sum(weights[:len(pipeline_orders)])
        order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * weighted_avg
    else:
        order_amount = base_order

    # Apply demand-responsive adjustment (more conservative)
    if pipeline_orders and len(pipeline_orders) >= 2:
        recent_trend = pipeline_orders[0] - pipeline_orders[1]
        adjustment = demand_forecast_factor * recent_trend
        # Limit adjustment magnitude to avoid overreaction
        max_adjustment = 0.2 * base_order
        adjustment = max(-max_adjustment, min(adjustment, max_adjustment))
        order_amount = max(0, order_amount + adjustment)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
