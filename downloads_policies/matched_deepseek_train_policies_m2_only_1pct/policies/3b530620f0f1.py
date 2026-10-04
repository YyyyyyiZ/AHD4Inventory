# policy_hash: 3b530620f0f16ddbfb429b428503e7452714347a146fe671092893f056bd5b7c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4613.39
# best_prompt_performance: 4613.38
# best_rel_error_pct: 0.000217
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_173355.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 439.7456067481284  # OPT_PARAM: {"initial": 439.7456067481284, "min": 300, "max": 600, "type": "float"}
    safety_stock = 55.13713795564406  # OPT_PARAM: {"initial": 55.13713795564406, "min": 0, "max": 100, "type": "float"}
    demand_smoothing = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    # Weight earlier arrivals more heavily since they're more certain
    weighted_pipeline = 0
    total_weight = 0
    for i, qty in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += qty * weight
        total_weight += weight

    effective_pipeline = weighted_pipeline / total_weight if total_weight > 0 else 0

    # Calculate demand forecast using exponential smoothing of pipeline arrivals
    # This gives more stable forecasts than simple averages
    forecast = demand_smoothing * effective_pipeline + (1 - demand_smoothing) * base_stock / 4.0

    # Adjust base stock based on forecast
    adjusted_base_stock = base_stock + 0.8 * forecast  # Fixed multiplier for stability

    # Calculate target inventory position with safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount with smoother adjustment
    gap = target_inventory - inventory_position
    if gap > 0:
        # Order the full gap but ensure it's not too large relative to forecast
        max_order = 2.5 * forecast
        order_amount = min(gap, max_order)
    else:
        order_amount = 0

    return order_amount
