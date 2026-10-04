# policy_hash: 3ee7c3b09ad16cbd6e18a6badf11786d45ac40d92f6fcda54ab93186de14b9b3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 10185.16
# best_prompt_performance: 10185.58
# best_rel_error_pct: 0.004124
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074722.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 374.60435724869365  # OPT_PARAM: {"initial": 374.60435724869365, "min": 300, "max": 500, "type": "float"}
    safety_stock = 22.304357248692433  # OPT_PARAM: {"initial": 22.304357248692433, "min": 15, "max": 60, "type": "float"}
    demand_forecast_factor = 0.5414844525080217  # OPT_PARAM: {"initial": 0.5414844525080217, "min": 0.35, "max": 0.65, "type": "float"}
    pipeline_coverage_factor = 0.78  # OPT_PARAM: {"initial": 0.78, "min": 0.6, "max": 0.95, "type": "float"}
    order_smoothing = 0.35048907484978054  # OPT_PARAM: {"initial": 0.35048907484978054, "min": 0.3, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.6546514053612376  # OPT_PARAM: {"initial": 1.6546514053612376, "min": 1.0, "max": 2.0, "type": "float"}
    pipeline_weight_factor = 0.2180780721340912  # OPT_PARAM: {"initial": 0.2180780721340912, "min": 0.15, "max": 0.4, "type": "float"}
    min_order_threshold = 8.0  # OPT_PARAM: {"initial": 8.0, "min": 3.0, "max": 15.0, "type": "float"}

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
    if order_amount < min_order_threshold and raw_order > 0:
        order_amount = min_order_threshold

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
