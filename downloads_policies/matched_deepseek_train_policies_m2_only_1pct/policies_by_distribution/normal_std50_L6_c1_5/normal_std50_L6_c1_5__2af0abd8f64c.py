# policy_hash: 2af0abd8f64c65d757608ec071f1909d334579264c26d5a2c46dbde1ecf61210
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 32
# source_prompt_files: 1
# best_target_performance: 7328.94
# best_prompt_performance: 7325.02
# best_rel_error_pct: 0.053487
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_183327.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 580.1319922089262  # OPT_PARAM: {"initial": 580.1319922089262, "min": 400, "max": 700, "type": "float"}
    safety_stock = 173.61542586404406  # OPT_PARAM: {"initial": 173.61542586404406, "min": 80, "max": 180, "type": "float"}
    demand_smoothing = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    adjustment_rate = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent pipeline arrivals (most recent 3 periods)
    if len(pipeline_orders) >= 3:
        # Use simple average of recent arrivals as demand estimate
        recent_arrivals = pipeline_orders[:3]
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals)
    else:
        # Fallback to base stock divided by lead time
        demand_estimate = base_stock / 6

    # Smooth demand estimate
    smoothed_demand = demand_smoothing * demand_estimate + (1 - demand_smoothing) * (base_stock / 6)

    # Adjust base stock based on smoothed demand
    adjusted_base = base_stock + 0.5 * (smoothed_demand * 6 - base_stock)

    # Calculate pipeline adjustment - more aggressive than historical policy
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adj = pipeline_factor * avg_pipeline

    # Target inventory position
    target = adjusted_base + safety_stock - pipeline_adj

    # Calculate order with adjustment rate
    raw_order = max(0, target - inventory_position)
    order_amount = int(round(adjustment_rate * raw_order))

    return order_amount
