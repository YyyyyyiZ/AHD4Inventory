# policy_hash: 635610d93b06ab219c089531bc83a4ee74bfb0f1c6fc30aa1146dae80fd15624
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 10209.32
# best_prompt_performance: 10209.32
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073703.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 354.0221517587816  # OPT_PARAM: {"initial": 354.0221517587816, "min": 200, "max": 450, "type": "float"}
    safety_stock = 27.799209008757355  # OPT_PARAM: {"initial": 27.799209008757355, "min": 10, "max": 60, "type": "float"}
    demand_forecast_factor = 0.5173814683622111  # OPT_PARAM: {"initial": 0.5173814683622111, "min": 0.15, "max": 0.6, "type": "float"}
    pipeline_coverage_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.6, "max": 1.1, "type": "float"}
    order_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.2758865042859133  # OPT_PARAM: {"initial": 1.2758865042859133, "min": 1.0, "max": 3.0, "type": "float"}

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

    # Adjust base stock based on demand estimate and lost sales weighting
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
