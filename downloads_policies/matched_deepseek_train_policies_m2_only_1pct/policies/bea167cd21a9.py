# policy_hash: bea167cd21a9e2de64e5a7a6b0c6300e695b8d178fe47d7c0eeedcecc4c939f6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 10277.48
# best_prompt_performance: 10277.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073116.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 318.8004842043398  # OPT_PARAM: {"initial": 318.8004842043398, "min": 200, "max": 450, "type": "float"}
    safety_stock = 23.50048420433941  # OPT_PARAM: {"initial": 23.50048420433941, "min": 10, "max": 60, "type": "float"}
    demand_forecast_factor = 0.43543621296100044  # OPT_PARAM: {"initial": 0.43543621296100044, "min": 0.2, "max": 0.6, "type": "float"}
    pipeline_coverage_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.7, "max": 1.1, "type": "float"}
    order_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    lost_sales_weight = 2.3372481154320557  # OPT_PARAM: {"initial": 2.3372481154320557, "min": 1.2, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of pipeline arrivals
    weighted_sum = 0
    weight_total = 0
    for i, q in enumerate(pipeline_orders):
        weight = pipeline_coverage_factor ** (len(pipeline_orders) - i - 1)
        weighted_sum += q * weight
        weight_total += weight

    if weight_total > 0:
        avg_pipeline = weighted_sum / weight_total
        demand_estimate = avg_pipeline * demand_forecast_factor
    else:
        demand_estimate = 0

    # Adjust base stock based on demand estimate and lost sales weight
    adjusted_base = base_stock + demand_estimate * lost_sales_weight

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    order_amount = raw_order * order_smoothing

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
