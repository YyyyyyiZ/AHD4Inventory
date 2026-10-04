# policy_hash: f70e21d2103a7759de5933a04d64de15d91d86691ba8e78cce2889ec914f2e61
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 13046.85
# best_prompt_performance: 13046.8
# best_rel_error_pct: 0.000383
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_100349.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.14288749943984  # OPT_PARAM: {"initial": 350.14288749943984, "min": 200, "max": 500, "type": "float"}
    safety_stock = 180.24407780044265  # OPT_PARAM: {"initial": 180.24407780044265, "min": 120, "max": 250, "type": "float"}
    pipeline_coverage = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_weight = 1.2321142860077356  # OPT_PARAM: {"initial": 1.2321142860077356, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate current demand rate from pipeline arrivals (recent orders reflect recent demand)
    # Use weighted average of recent pipeline orders
    if len(pipeline_orders) >= 3:
        recent_weights = [0.5, 0.3, 0.2]  # More weight to most recent
        weighted_sum = sum(w * o for w, o in zip(recent_weights, pipeline_orders[:3]))
        demand_estimate = weighted_sum / sum(recent_weights[:len(pipeline_orders[:3])])
    else:
        demand_estimate = sum(pipeline_orders) / max(1, len(pipeline_orders))

    # Adjust base stock based on demand estimate
    adjusted_base = base_stock * (1 - demand_smoothing) + demand_estimate * demand_smoothing

    # Increase safety stock when lost sales are costly (p > h)
    adjusted_safety = safety_stock * lost_sales_weight

    # Order-up-to level with safety buffer
    order_up_to = adjusted_base + adjusted_safety

    # Order amount: cover gap to order-up-to, but discount existing pipeline
    # pipeline_coverage controls how much pipeline inventory we count
    effective_pipeline = pipeline_coverage * sum(pipeline_orders)
    order_amount = max(0, order_up_to - (on_hand_inventory + effective_pipeline))

    # Round to nearest integer (orders are discrete)
    return order_amount
