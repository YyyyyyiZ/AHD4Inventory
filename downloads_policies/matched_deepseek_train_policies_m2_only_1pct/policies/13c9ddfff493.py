# policy_hash: 13c9ddfff4930e2ba4815e4058933af852ac20eb267486150baf09190052cab8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10410.82
# best_prompt_performance: 10421.64
# best_rel_error_pct: 0.103930
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072837.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.8224935025985  # OPT_PARAM: {"initial": 280.8224935025985, "min": 100, "max": 500, "type": "float"}
    safety_stock = 40.82249350259872  # OPT_PARAM: {"initial": 40.82249350259872, "min": 10, "max": 100, "type": "float"}
    demand_forecast_factor = 0.2816130135736404  # OPT_PARAM: {"initial": 0.2816130135736404, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_coverage_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}
    order_smoothing = 0.5830707904293303  # OPT_PARAM: {"initial": 0.5830707904293303, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of pipeline arrivals
    # Give more weight to recent arrivals
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

    # Adjust base stock based on demand estimate
    adjusted_base = base_stock + demand_estimate

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    order_amount = raw_order * order_smoothing

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
