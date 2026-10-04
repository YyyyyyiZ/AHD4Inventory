# policy_hash: 4696d62e5c3e2b836218f7d7f33f375fab206fc60253d9f56a3ae515d4a8491e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6732.48
# best_prompt_performance: 6732.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235538.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 341.45071126136065  # OPT_PARAM: {"initial": 341.45071126136065, "min": 100, "max": 800, "type": "float"}
    safety_stock = 70.54782664019625  # OPT_PARAM: {"initial": 70.54782664019625, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.01, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent arrivals
    # Give more weight to most recent arrivals
    if len(pipeline_orders) >= 3:
        # Use last 3 arrivals with weights [0.5, 0.3, 0.2]
        weights = [0.5, 0.3, 0.2]
        recent_arrivals = pipeline_orders[:3]
        weighted_sum = sum(w * d for w, d in zip(weights, recent_arrivals))
        avg_recent_demand = weighted_sum
    else:
        # Fallback to simple average
        avg_recent_demand = sum(pipeline_orders[:2]) / 2 if len(pipeline_orders) >= 2 else base_stock / 4

    # Adjust base stock based on demand trend
    # Use smaller adjustment factor to avoid overreacting
    demand_adjustment = demand_forecast_factor * (avg_recent_demand - base_stock/4)
    adjusted_base_stock = base_stock + demand_adjustment

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
