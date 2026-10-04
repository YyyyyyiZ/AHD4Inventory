# policy_hash: 83fe180dde2e13316b375af5e657e934a90d49d0780d307ea6da1f26fe409e92
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 10210.52
# best_prompt_performance: 10210.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073552.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 345.082195493535  # OPT_PARAM: {"initial": 345.082195493535, "min": 250, "max": 450, "type": "float"}
    safety_stock = 35.08219549353395  # OPT_PARAM: {"initial": 35.08219549353395, "min": 20, "max": 80, "type": "float"}
    demand_forecast_factor = 0.3245308322821877  # OPT_PARAM: {"initial": 0.3245308322821877, "min": 0.3, "max": 0.7, "type": "float"}
    pipeline_coverage_factor = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.7, "max": 1.0, "type": "float"}
    order_smoothing = 0.41622124333185073  # OPT_PARAM: {"initial": 0.41622124333185073, "min": 0.4, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.6297176682659151  # OPT_PARAM: {"initial": 1.6297176682659151, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_weight_factor = 0.16823067020090016  # OPT_PARAM: {"initial": 0.16823067020090016, "min": 0.1, "max": 0.5, "type": "float"}

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

    # Add pipeline coverage adjustment
    pipeline_coverage = sum(pipeline_orders) * pipeline_weight_factor
    target_inventory = adjusted_base + safety_stock - pipeline_coverage

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    order_amount = raw_order * order_smoothing

    # Ensure minimum order quantity for responsiveness
    if order_amount < 5 and raw_order > 0:
        order_amount = 5

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
